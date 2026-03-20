from __future__ import annotations

import re
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

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


def _line_has_italic_ansi(value: str) -> bool:
    return "\x1b[3m" in value or "\x1b[23m" in value


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


def _run_pi(job_id: str, prompt: str, model: str, session_name: str, api_key_env: str | None = None, api_key_value: str | None = None) -> int:
    """Run job using pi-coding-agent (pi) CLI."""
    token = uuid.uuid4().hex[:8]
    model_base, thinking_level = _split_model_and_thinking(model)

    # Build pi command
    pi_bin = "/home/alyssonpi/.npm-global/bin/pi"
    # Use single quotes for the whole prompt to avoid shell expansion issues

    _ensure_session(session_name, str(REPO_ROOT))
    if not api_key_env and model_base:
        provider = model_base.split("/", 1)[0].split(":", 1)[0].strip()
        if provider:
            provider_norm = re.sub(r"[^A-Za-z0-9]", "_", provider).upper()
            api_key_env = f"{provider_norm}_API_KEY"

    if api_key_env and api_key_value is None:
        import os

        api_key_value = os.environ.get(api_key_env)

    prefix = ""
    if api_key_env and api_key_value is not None:
        prefix = f"export {api_key_env}={shlex.quote(api_key_value)} && "

    pi_cmd_str = prefix + f"{pi_bin} -p '{prompt}'"

    # Add model if specified
    if model_base:
        pi_cmd_str += f" --model '{model_base}'"
    if thinking_level:
        pi_cmd_str += f" --thinking {thinking_level}"

    pi_output_file = Path(f"{PI_OUTPUT_PREFIX}{job_id}.txt")
    wrapped_cmd = (
        f'echo "{START_PREFIX}{token}" ; '
        + pi_cmd_str
        + f" > {shlex.quote(str(pi_output_file))} 2>&1 ; "
        + f'echo "{SENTINEL_PREFIX}{token}:$?"'
    )
    _send_keys(session_name, wrapped_cmd)
    return _wait_for_sentinel(session_name, token)


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

    _write_yaml(job_file, data)

    exit_code = 1
    try:
        if agent == "pi":
            exit_code = runner(job_id, prompt, model, session_name, api_key_env, api_key_value)
        else:
            exit_code = runner(job_id, prompt, model, session_name)
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
                        if _line_has_italic_ansi(raw_line):
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

                    if blocks:
                        data["summary"] = '\n'.join(blocks[-1][-20:])[:4000]
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
