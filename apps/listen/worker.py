from __future__ import annotations

import json
import base64
import mimetypes
import re
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

SENTINEL_PREFIX = "__JOBDONE_"
START_PREFIX = "__JOBSTART_"
POLL_INTERVAL = 2.0

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
REPO_ROOT = BASE_DIR.parent.parent
CODEX_SYSTEM_PROMPT = REPO_ROOT / ".opencode" / "agents" / "job-system-prompt.md"
CODEX_USER_PROMPT = REPO_ROOT / ".opencode" / "commands" / "rpi-gui-term-user-prompt.md"
PI_OUTPUT_PREFIX = "/tmp/listen-pi-output-"

_THINKING_LEVELS = {"off", "minimal", "low", "medium", "high", "xhigh"}
_INLINE_SECRET_PATTERNS = [
    re.compile(r"\bsk-or-v1-[A-Za-z0-9._-]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9._-]{12,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|authorization|bearer)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)\b[A-Z0-9_]*KEY\s*=\s*['\"]?[^'\"\s]+"),
]
_SENSITIVE_LINE_HINTS = re.compile(r"(?i)\b(api[_-]?key|authorization|bearer|token|secretctl_password)\b")
_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
_LMSTUDIO_FALLBACK_BASE_URLS = (
    "http://192.168.0.18:1234/v1",
    "http://100.93.136.48:1234/v1",
)


def _split_model_and_thinking(model: str) -> tuple[str, str | None]:
    if not model or ":" not in model:
        return model, None
    base, suffix = model.rsplit(":", 1)
    suffix = suffix.strip()
    if suffix in _THINKING_LEVELS:
        return base, suffix
    return model, None


def _sanitize_text(value: str) -> str:
    sanitized = value
    for pattern in _INLINE_SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def _extract_between_markers(captured: str) -> str:
    lines = captured.splitlines()
    start_index = -1
    end_index = len(lines)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(START_PREFIX):
            start_index = idx
        if stripped.startswith(SENTINEL_PREFIX):
            end_index = idx
            break

    if start_index >= 0:
        return "\n".join(lines[start_index + 1:end_index])
    return captured


def _line_is_sensitive(line: str) -> bool:
    if _SENSITIVE_LINE_HINTS.search(line):
        return True
    return any(pattern.search(line) for pattern in _INLINE_SECRET_PATTERNS)


def _strip_ansi(value: str) -> str:
    return _ANSI_ESCAPE_PATTERN.sub("", value)


def _normalize_lmstudio_base_url(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        return ""
    return cleaned if cleaned.endswith("/v1") else f"{cleaned.rstrip('/')}/v1"


def _candidate_lmstudio_base_urls(preferred: str | None = None) -> list[str]:
    candidates: list[str] = []
    for raw in [preferred, *_LMSTUDIO_FALLBACK_BASE_URLS]:
        if not raw:
            continue
        normalized = _normalize_lmstudio_base_url(raw)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def _lmstudio_base_url_reachable(base_url: str, timeout_seconds: float = 3.0) -> bool:
    try:
        request = Request(
            f"{base_url}/models",
            headers={"Authorization": "Bearer dummy"},
            method="GET",
        )
        with urlopen(request, timeout=timeout_seconds):
            return True
    except Exception:
        return False


def _resolve_lmstudio_base_url(preferred: str | None = None) -> str:
    candidates = _candidate_lmstudio_base_urls(preferred)
    for candidate in candidates:
        if _lmstudio_base_url_reachable(candidate):
            return candidate
    return candidates[0] if candidates else "http://192.168.0.18:1234/v1"


def _score_pi_summary_block(lines: list[str]) -> tuple[int, int]:
    joined = "\n".join(lines)
    lowered = joined.lower()
    score = 0
    if "{" in joined and "}" in joined:
        score += 4
    if '"summary"' in joined:
        score += 3
    if any(token in joined for token in ['"confidence"', '"risk_score"', '"material_class"']):
        score += 3
    if "warning:" in lowered:
        score -= 3
    if "model" in lowered and "not found" in lowered:
        score -= 4
    return score, len(lines)


def _extract_json_object_from_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL | re.IGNORECASE)
    if fence_match:
        stripped = fence_match.group(1).strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for index, ch in enumerate(stripped):
        if ch != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    return None


def _tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], capture_output=True, text=True, check=check)


def _session_exists(name: str) -> bool:
    return _tmux("has-session", "-t", name, check=False).returncode == 0


def _ensure_session(name: str, cwd: str) -> None:
    if _session_exists(name):
        return
    _tmux("new-session", "-d", "-s", name, "-c", cwd)
    # Ensure DISPLAY is set for the session
    _send_keys(name, "export DISPLAY=:0")


def _send_keys(session: str, keys: str) -> None:
    _tmux("send-keys", "-t", f"{session}:", keys, "C-m")


def _capture_pane(session: str) -> str:
    return _tmux("capture-pane", "-p", "-t", f"{session}:", "-S", "-1000").stdout


def _wait_for_sentinel(session: str, token: str) -> int:
    pattern = re.compile(rf"^{re.escape(SENTINEL_PREFIX)}{token}:(\d+)\s*$", re.MULTILINE)
    while True:
        time.sleep(POLL_INTERVAL)
        captured = _capture_pane(session)
        match = pattern.search(captured)
        if match:
            return int(match.group(1))


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _render_prompt(job_id: str, user_prompt: str) -> str:
    system_prompt = CODEX_SYSTEM_PROMPT.read_text(encoding="utf-8").replace("{{JOB_ID}}", job_id)
    command_prompt = CODEX_USER_PROMPT.read_text(encoding="utf-8").replace("$ARGUMENTS", user_prompt)
    return f"{system_prompt}\n\n---\n\n{command_prompt}\n"


def _normalize_image_attachments(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    attachments: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if cleaned and cleaned not in attachments:
            attachments.append(cleaned)
    return attachments


def _build_prompt_with_images(prompt: str, image_attachments: list[str]) -> str:
    if not image_attachments:
        return prompt
    attachments_block = "\n".join(f"- {image_path}" for image_path in image_attachments)
    return (
        f"{prompt.rstrip()}\n\n"
        "Use the images below as additional context for this task.\n"
        "Image attachments:\n"
        f"{attachments_block}"
    )


def _run_codex(job_id: str, prompt: str, model: str, session_name: str) -> int:
    """Run job using codex exec (original implementation)."""
    token = uuid.uuid4().hex[:8]
    prompt_file = Path(f"/tmp/listen-codex-prompt-{job_id}.md")
    output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
    prompt_file.write_text(_render_prompt(job_id, prompt), encoding="utf-8")

    # Build codex command with optional model
    codex_cmd = (
        f"cd '{REPO_ROOT}' && "
        f"codex exec --dangerously-bypass-approvals-and-sandbox "
        f"--skip-git-repo-check -C '{REPO_ROOT}' "
    )

    if model:
        codex_cmd += f"-c model='{model}' "

    codex_cmd += f"-o '{output_file}' - < '{prompt_file}'"

    wrapped = f'echo "{START_PREFIX}{token}" ; {codex_cmd} ; echo "{SENTINEL_PREFIX}{token}:$?"'

    _ensure_session(session_name, str(REPO_ROOT))
    _send_keys(session_name, wrapped)
    return _wait_for_sentinel(session_name, token)


def _run_openclaw(job_id: str, prompt: str, model: str, session_name: str) -> int:
    """Run job using OpenClaw agent CLI (same as openclaw-listen)."""
    token = uuid.uuid4().hex[:8]

    # Build OpenClaw command - use 'openclaw agent' wrapper
    # Quote the prompt to preserve spaces
    prompt_quoted = f'"{prompt}"' if ' ' in prompt else prompt
    openclaw_cmd = f"openclaw agent --agent main --message {prompt_quoted}"

    if model:
        openclaw_cmd += f" --model '{model}'"

    # Wrap with sentinel
    wrapped = f'echo "{START_PREFIX}{token}" ; {openclaw_cmd} ; echo "{SENTINEL_PREFIX}{token}:$?"'

    _ensure_session(session_name, str(REPO_ROOT))
    _send_keys(session_name, wrapped)
    return _wait_for_sentinel(session_name, token)


def _run_opencode(job_id: str, prompt: str, model: str, session_name: str) -> int:
    """Run job using OpenCode CLI."""
    token = uuid.uuid4().hex[:8]

    # Build opencode command
    opencode_bin = Path.home() / ".opencode" / "bin" / "opencode"

    if not opencode_bin.exists():
        raise FileNotFoundError(f"OpenCode binary not found at {opencode_bin}")

    opencode_cmd = [
        str(opencode_bin),
        "run",
        prompt,
    ]

    # Add model selection if specified
    if model:
        opencode_cmd.extend(["--model", model])

    # Wrap with sentinel
    wrapped_cmd = f'echo "{START_PREFIX}{token}" ; ' + ' '.join([str(c) for c in opencode_cmd]) + f' ; echo "{SENTINEL_PREFIX}{token}:$?"'

    _ensure_session(session_name, str(REPO_ROOT))
    _send_keys(session_name, wrapped_cmd)
    return _wait_for_sentinel(session_name, token)


def _partition_pi_attachments(image_attachments: list[str]) -> tuple[list[str], list[str]]:
    file_attachments: list[str] = []
    reference_attachments: list[str] = []
    for attachment in image_attachments:
        candidate = Path(attachment)
        if candidate.exists() and candidate.is_file():
            file_attachments.append(str(candidate))
        else:
            reference_attachments.append(attachment)
    return file_attachments, reference_attachments


def _prepare_pi_file_attachments(
    job_id: str,
    provider_norm: str | None,
    file_attachments: list[str],
) -> tuple[list[str], list[Path]]:
    if provider_norm != "LMSTUDIO" or not file_attachments:
        return file_attachments, []
    try:
        from PIL import Image
    except Exception:
        return file_attachments, []
    import os

    max_side_raw = (os.environ.get("LMSTUDIO_IMAGE_MAX_SIDE") or "768").strip()
    try:
        max_side = int(max_side_raw)
    except ValueError:
        max_side = 768
    max_side = max(256, min(max_side, 2048))
    prepared: list[str] = []
    temp_files: list[Path] = []
    for index, attachment in enumerate(file_attachments, start=1):
        source = Path(attachment)
        if not source.exists() or not source.is_file():
            prepared.append(attachment)
            continue
        try:
            with Image.open(source) as image:
                width, height = image.size
                if max(width, height) <= max_side:
                    prepared.append(attachment)
                    continue
                converted = image.convert("RGB")
                converted.thumbnail((max_side, max_side))
                target = Path(f"/tmp/listen-pi-image-{job_id}-{index}.jpg")
                converted.save(target, format="JPEG", quality=85, optimize=True)
                prepared.append(str(target))
                temp_files.append(target)
        except Exception:
            prepared.append(attachment)
    return prepared, temp_files


def _infer_provider_norm(model_base: str) -> str | None:
    if not model_base:
        return None
    provider = model_base.split("/", 1)[0].split(":", 1)[0].strip()
    if not provider:
        return None
    return re.sub(r"[^A-Za-z0-9]", "_", provider).upper()


def _resolve_provider_extension(provider_norm: str | None) -> str | None:
    if not provider_norm:
        return None
    import os

    specific_env = os.environ.get(f"{provider_norm}_EXTENSION_PATH")
    if specific_env:
        candidate = Path(specific_env).expanduser()
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    if provider_norm == "LMSTUDIO":
        candidates = [
            Path.home() / ".openclaw" / "workspace" / "rcc-agents-ifes" / "application" / "pi-extensions" / "lmstudio.ts",
            Path.home() / "Github" / "rcc-agents-ifes" / "application" / "pi-extensions" / "lmstudio.ts",
            REPO_ROOT / "application" / "pi-extensions" / "lmstudio.ts",
            REPO_ROOT.parent / "rcc-agents-ifes" / "application" / "pi-extensions" / "lmstudio.ts",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
    return None


def _encode_lmstudio_image_attachment(path: str) -> dict[str, object]:
    image_path = Path(path)
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{payload}",
        },
    }


def _run_lmstudio_vision_direct(
    job_id: str,
    prompt: str,
    model_base: str,
    file_attachments: list[str],
) -> int:
    import os

    request_model = model_base.split("/", 1)[1] if model_base.startswith("lmstudio/") else model_base
    api_key = os.environ.get("LMSTUDIO_API_KEY") or "dummy"
    timeout_raw = (os.environ.get("LMSTUDIO_VISION_TIMEOUT_SECONDS") or "120").strip()
    try:
        timeout_seconds = max(30, int(timeout_raw))
    except ValueError:
        timeout_seconds = 120

    user_content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
    for attachment in file_attachments:
        candidate = Path(attachment)
        if candidate.exists() and candidate.is_file():
            user_content.append(_encode_lmstudio_image_attachment(str(candidate)))

    body = {
        "model": request_model,
        "messages": [
            {
                "role": "system",
                "content": "Return only the final answer requested by the user.",
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "chat_template_kwargs": {
            "enable_thinking": False,
        },
        "stream": True,
        "stream_options": {
            "include_usage": True,
        },
        "store": False,
        "max_completion_tokens": 8192,
        "tools": [],
    }
    output_path = Path(f"{PI_OUTPUT_PREFIX}{job_id}.txt")
    connection_errors: list[str] = []
    base_url_candidates = _candidate_lmstudio_base_urls(os.environ.get("LMSTUDIO_BASE_URL"))
    for base_url in base_url_candidates:
        endpoint = f"{base_url}/chat/completions"
        request = Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                collected_parts: list[str] = []
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for choice in event.get("choices") or []:
                        delta = choice.get("delta") or {}
                        content_piece = delta.get("content")
                        if isinstance(content_piece, str):
                            collected_parts.append(content_piece)
                        elif isinstance(content_piece, list):
                            for item in content_piece:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    collected_parts.append(str(item.get("text", "")))
            content = "".join(collected_parts).strip()
            if content:
                os.environ["LMSTUDIO_BASE_URL"] = base_url
                output_path.write_text(content, encoding="utf-8")
                return 0
            output_path.write_text("LM Studio returned no content.", encoding="utf-8")
            return 1
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            output_path.write_text(f"LM Studio HTTP error {exc.code}: {detail or exc.reason}", encoding="utf-8")
            return 1
        except URLError as exc:
            connection_errors.append(f"{base_url}: {exc.reason}")
        except Exception as exc:
            connection_errors.append(f"{base_url}: {exc}")
    if connection_errors:
        output_path.write_text(
            "LM Studio connection failed: " + " | ".join(connection_errors),
            encoding="utf-8",
        )
        return 1

    output_path.write_text("LM Studio connection failed: no candidate base URL available.", encoding="utf-8")
    return 1


def _run_pi(
    job_id: str,
    prompt: str,
    model: str,
    session_name: str,
    api_key_env: str | None = None,
    api_key_value: str | None = None,
    image_attachments: list[str] | None = None,
) -> int:
    """Run job using pi-coding-agent (pi) CLI."""
    token = uuid.uuid4().hex[:8]
    model_base, thinking_level = _split_model_and_thinking(model)
    provider_norm = _infer_provider_norm(model_base)

    image_attachments = image_attachments or []
    file_attachments, reference_attachments = _partition_pi_attachments(image_attachments)
    file_attachments, temp_image_files = _prepare_pi_file_attachments(
        job_id=job_id,
        provider_norm=provider_norm,
        file_attachments=file_attachments,
    )
    prompt_text = _build_prompt_with_images(prompt, reference_attachments)

    # Build pi command
    pi_bin = "/home/alyssonpi/.npm-global/bin/pi"

    _ensure_session(session_name, str(REPO_ROOT))
    extension_path = _resolve_provider_extension(provider_norm)
    if not api_key_env and provider_norm:
        api_key_env = f"{provider_norm}_API_KEY"
    base_url_env = f"{provider_norm}_BASE_URL" if provider_norm else None

    if api_key_env and api_key_value is None:
        import os

        api_key_value = os.environ.get(api_key_env)
    base_url_value = None
    if base_url_env:
        import os

        base_url_value = os.environ.get(base_url_env)
    if provider_norm == "LMSTUDIO":
        base_url_value = _resolve_lmstudio_base_url(base_url_value)

    prefix_parts: list[str] = []
    if api_key_env and api_key_value is not None:
        prefix_parts.append(f"export {api_key_env}={shlex.quote(api_key_value)}")
    if base_url_env and base_url_value:
        prefix_parts.append(f"export {base_url_env}={shlex.quote(base_url_value)}")
    prefix = f"{' && '.join(prefix_parts)} && " if prefix_parts else ""

    pi_cmd_parts = [pi_bin]

    # Add model if specified
    if extension_path:
        pi_cmd_parts.extend(["--extension", extension_path])
    if model_base:
        pi_cmd_parts.extend(["--model", model_base])
    if provider_norm == "LMSTUDIO":
        pi_cmd_parts.append("--no-tools")
    if thinking_level:
        pi_cmd_parts.extend(["--thinking", thinking_level])
    pi_cmd_parts.append("-p")
    pi_cmd_parts.extend([f"@{path}" for path in file_attachments])
    pi_cmd_parts.append(prompt_text)

    pi_cmd_str = prefix + " ".join(shlex.quote(part) for part in pi_cmd_parts)

    try:
        if provider_norm == "LMSTUDIO" and file_attachments:
            return _run_lmstudio_vision_direct(
                job_id=job_id,
                prompt=prompt_text,
                model_base=model_base,
                file_attachments=file_attachments,
            )

        pi_output_file = Path(f"{PI_OUTPUT_PREFIX}{job_id}.txt")
        wrapped_cmd = (
            f'echo "{START_PREFIX}{token}" ; '
            + pi_cmd_str
            + f" > {shlex.quote(str(pi_output_file))} 2>&1 ; "
            + f'echo "{SENTINEL_PREFIX}{token}:$?"'
        )
        _send_keys(session_name, wrapped_cmd)
        return _wait_for_sentinel(session_name, token)
    finally:
        for temp_file in temp_image_files:
            temp_file.unlink(missing_ok=True)


# Agent runners mapping
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,  # claude maps to OpenClaw for now
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,
    "pi": _run_pi,
}


def main(
    job_id: str,
    prompt: str,
    agent: str = "codex",
    model: str = "",
    api_key_env: str | None = None,
    api_key_value: str | None = None,
) -> None:
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise SystemExit(f"Job file not found: {job_id}")

    # Validate prompts exist for codex
    if agent == "codex":
        if not CODEX_SYSTEM_PROMPT.exists():
            raise SystemExit(f"Missing system prompt: {CODEX_SYSTEM_PROMPT}")
        if not CODEX_USER_PROMPT.exists():
            raise SystemExit(f"Missing user prompt: {CODEX_USER_PROMPT}")

    session_name = f"job-{job_id}"

    # Debug: Log BEFORE getting runner
    debug_log = Path("/tmp/worker-debug.log")
    with open(debug_log, "a") as f:
        f.write(f"[{job_id}] agent={agent}, session={session_name}\n")

    # Get agent runner
    runner = AGENT_RUNNERS.get(agent)
    if not runner:
        with open(debug_log, "a") as f:
            f.write(f"[{job_id}] ERROR: runner=None for agent={agent}\n")
        raise SystemExit(f"Unknown agent: {agent}. Available: {', '.join(AGENT_RUNNERS.keys())}")

    # Debug: Log AFTER getting runner
    with open(debug_log, "a") as f:
        f.write(f"[{job_id}] runner={runner.__name__}\n")

    start_time = time.time()
    data = _read_yaml(job_file)
    image_attachments = _normalize_image_attachments(data.get("image_attachments"))
    prompt_with_images = _build_prompt_with_images(prompt, image_attachments)
    data["session"] = session_name

    # Log which agent is being used
    if agent == "claude":
        agent_display = "OpenCode (claude compatibility mode)"
    elif agent == "openclaw":
        agent_display = "OpenClaw agent CLI"
    elif agent == "opencode":
        agent_display = "OpenCode CLI"
    elif agent == "pi":
        agent_display = "Pi coding agent"
    else:
        agent_display = f"{agent.capitalize()}"

    if model:
        data.setdefault("updates", []).append(f"Spawned {agent_display} worker using model: {model}")
    else:
        data.setdefault("updates", []).append(f"Spawned {agent_display} worker with default model")
    if image_attachments:
        data.setdefault("updates", []).append(f"Attached {len(image_attachments)} image(s) to prompt context")
    if agent == "pi" and image_attachments:
        pi_file_attachments, pi_reference_attachments = _partition_pi_attachments(image_attachments)
        if pi_file_attachments:
            data.setdefault("updates", []).append(
                f"PI received {len(pi_file_attachments)} file attachment(s) via @file"
            )
        if pi_reference_attachments:
            data.setdefault("updates", []).append(
                f"PI received {len(pi_reference_attachments)} non-file attachment reference(s) in prompt"
            )

    _write_yaml(job_file, data)

    exit_code = 1
    try:
        if agent == "pi":
            exit_code = runner(job_id, prompt, model, session_name, api_key_env, api_key_value, image_attachments)
        else:
            exit_code = runner(job_id, prompt_with_images, model, session_name)
    except Exception as exc:
        data = _read_yaml(job_file)
        data["status"] = "failed"
        data["summary"] = str(exc)
        data.setdefault("updates", []).append(f"Worker failed before completion: {exc}")
        _write_yaml(job_file, data)
    finally:
        duration = round(time.time() - start_time)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = _read_yaml(job_file)
        if data.get("status") == "running":
            data["status"] = "completed" if exit_code == 0 else "failed"
            data["exit_code"] = exit_code
            data["duration_seconds"] = duration
            data["completed_at"] = now

            # Capture summary if not already set
            if not data.get("summary"):
                if agent == "codex":
                    # Read output file for codex
                    output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
                    if output_file.exists():
                        data["summary"] = output_file.read_text(encoding="utf-8").strip()[:4000]
                elif agent == "pi":
                    pi_output_file = Path(f"{PI_OUTPUT_PREFIX}{job_id}.txt")
                    captured = ""
                    if pi_output_file.exists():
                        captured = pi_output_file.read_text(encoding="utf-8", errors="replace")
                    if not captured and _session_exists(session_name):
                        captured = _extract_between_markers(_capture_pane(session_name))
                    blocks: list[list[str]] = []
                    current_block: list[str] = []

                    for raw_line in captured.split('\n'):
                        line = _strip_ansi(raw_line).rstrip()
                        if not line:
                            if current_block:
                                blocks.append(current_block)
                                current_block = []
                            continue
                        if _line_is_sensitive(line):
                            continue
                        if line.strip().startswith("export DISPLAY="):
                            continue
                        if "API_KEY" in line:
                            continue
                        if START_PREFIX in line or SENTINEL_PREFIX in line or ':$?' in line or ':$\'"' in line:
                            continue
                        if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
                            continue
                        if any(p in line for p in ['/bin/pi', 'pi -p']):
                            continue
                        if any(p in line for p in ['listen-pi-output-', '--model', '.npm-global/bin/pi']):
                            continue
                        current_block.append(_sanitize_text(line))

                    if current_block:
                        blocks.append(current_block)

                    best_json_summary = ""
                    best_json_score: tuple[int, int] | None = None
                    for block in blocks:
                        candidate_json = _extract_json_object_from_text("\n".join(block))
                        if not candidate_json:
                            continue
                        candidate_score = _score_pi_summary_block(block)
                        if best_json_score is None or candidate_score > best_json_score:
                            best_json_score = candidate_score
                            best_json_summary = candidate_json

                    if best_json_summary:
                        data["summary"] = best_json_summary[:4000]
                    else:
                        candidate_json = _extract_json_object_from_text(captured) if captured else ""
                        if candidate_json:
                            data["summary"] = candidate_json[:4000]
                            captured = ""
                        elif blocks:
                            selected_block = max(blocks, key=_score_pi_summary_block)
                            data["summary"] = '\n'.join(selected_block[-20:])[:4000]
                    if captured and not data.get("summary"):
                        raw_lines: list[str] = []
                        for raw_line in captured.split('\n'):
                            line = _sanitize_text(_strip_ansi(raw_line).rstrip())
                            if not line:
                                continue
                            if _line_is_sensitive(line):
                                continue
                            if "API_KEY" in line:
                                continue
                            raw_lines.append(line)
                        if raw_lines:
                            data["summary"] = '\n'.join(raw_lines[-20:])[:4000]
                elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
                    # Capture tmux output for opencode/openclaw
                    captured = _extract_between_markers(_capture_pane(session_name))
                    lines = []

                    for line in captured.split('\n'):
                        line = line.rstrip()
                        # Skip empty lines
                        if not line:
                            continue
                        if _line_is_sensitive(line):
                            continue
                        if line.strip().startswith("export DISPLAY="):
                            continue
                        if "API_KEY" in line:
                            continue
                        # Skip sentinel and its remnants
                        if SENTINEL_PREFIX in line or ':$?' in line or ':$\'"' in line:
                            continue
                        # Skip command prompts
                        if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
                            continue
                        # Skip lines with binary paths or command prefixes
                        if any(p in line for p in ['/bin/opencode', 'opencode run', '/bin/pi', 'pi -p']):
                            continue
                        lines.append(_sanitize_text(line))

                    # Take last 20 useful lines
                    if lines:
                        data["summary"] = '\n'.join(lines[-20:])[:4000]

            if data.get("summary"):
                data["summary"] = _sanitize_text(str(data["summary"]))[:4000]
            elif data.get("status") == "completed":
                data["summary"] = "Job completed successfully (no textual output captured)."
            else:
                data["summary"] = f"Job failed with exit code {exit_code} (no textual output captured)."

            _write_yaml(job_file, data)

        # Cleanup
        prompt_file = Path(f"/tmp/listen-codex-prompt-{job_id}.md")
        output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
        pi_output_file = Path(f"{PI_OUTPUT_PREFIX}{job_id}.txt")
        prompt_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)
        pi_output_file.unlink(missing_ok=True)
        if _session_exists(session_name):
            _tmux("kill-session", "-t", session_name, check=False)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("Usage: worker.py <job_id> <prompt> <agent> [model]")
    job_id = sys.argv[1]
    prompt = sys.argv[2]
    agent = sys.argv[3] if len(sys.argv) > 3 else "codex"
    model = sys.argv[4] if len(sys.argv) > 4 else ""
    import os
    api_key_env = os.environ.get("LISTEN_API_KEY_ENV") or (sys.argv[5] if len(sys.argv) > 5 else None)
    api_key_value = os.environ.get("LISTEN_API_KEY") or (sys.argv[6] if len(sys.argv) > 6 else None)
    debug_log = Path("/tmp/worker-debug.log")
    with open(debug_log, "a") as f:
        f.write(f"[{job_id}] agent={agent}, model={model}, api_key_env={api_key_env}, api_key_present={bool(api_key_value)}\n")
    main(job_id, prompt, agent, model, api_key_env, api_key_value)
