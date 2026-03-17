from __future__ import annotations

import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

SENTINEL_PREFIX = "__JOBDONE_"
POLL_INTERVAL = 2.0

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
REPO_ROOT = BASE_DIR.parent
CODEX_SYSTEM_PROMPT = REPO_ROOT / ".opencode" / "agents" / "job-system-prompt.md"
CODEX_USER_PROMPT = REPO_ROOT / ".opencode" / "commands" / "rpi-gui-term-user-prompt.md"


def _tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], capture_output=True, text=True, check=check)


def _session_exists(name: str) -> bool:
    return _tmux("has-session", "-t", name, check=False).returncode == 0


def _ensure_session(name: str, cwd: str) -> None:
    if _session_exists(name):
        return
    _tmux("new-session", "-d", "-s", name, "-c", cwd)


def _send_keys(session: str, keys: str) -> None:
    _tmux("send-keys", "-t", f"{session}:", keys)
    _tmux("send-keys", "-t", f"{session}:", "Enter")


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

    wrapped = f'{codex_cmd} ; echo "{SENTINEL_PREFIX}{token}:$?"'

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
    wrapped = f'{openclaw_cmd} ; echo "{SENTINEL_PREFIX}{token}:$?"'

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

    # TODO: Add model support when opencode supports it
    # if model:
    #     opencode_cmd.extend(["--model", model])

    # Wrap with sentinel
    wrapped_cmd = ' '.join([str(c) for c in opencode_cmd]) + f' ; echo "{SENTINEL_PREFIX}{token}:$?"'

    _ensure_session(session_name, str(REPO_ROOT))
    _send_keys(session_name, wrapped_cmd)
    return _wait_for_sentinel(session_name, token)


# Agent runners mapping
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,  # claude maps to OpenClaw for now
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,
}


def main(job_id: str, prompt: str, agent: str = "codex", model: str = "") -> None:
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

    # Get agent runner
    runner = AGENT_RUNNERS.get(agent)
    if not runner:
        raise SystemExit(f"Unknown agent: {agent}. Available: {', '.join(AGENT_RUNNERS.keys())}")

    start_time = time.time()
    data = _read_yaml(job_file)
    data["session"] = session_name

    # Debug: Log which runner was selected
    debug_log = Path("/tmp/worker-debug.log")
    with open(debug_log, "a") as f:
        f.write(f"[{job_id}] runner={runner.__name__}, agent={agent}\n")

    # Log which agent is being used
    if agent == "claude":
        agent_display = "OpenCode (claude compatibility mode)"
    elif agent == "openclaw":
        agent_display = "OpenClaw agent CLI"
    elif agent == "opencode":
        agent_display = "OpenCode CLI"
    else:
        agent_display = f"{agent.capitalize()}"

    if model:
        data.setdefault("updates", []).append(f"Spawned {agent_display} worker using model: {model}")
    else:
        data.setdefault("updates", []).append(f"Spawned {agent_display} worker with default model")

    _write_yaml(job_file, data)

    exit_code = 1
    try:
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
                elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
                    # Capture tmux output for opencode/openclaw
                    captured = _capture_pane(session_name)
                    lines = []

                    for line in captured.split('\n'):
                        line = line.rstrip()
                        # Skip empty lines
                        if not line:
                            continue
                        # Skip sentinel
                        if SENTINEL_PREFIX in line:
                            continue
                        # Skip command prompts
                        if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
                            continue
                        # Skip lines with binary paths or opencode command
                        if '/bin/opencode' in line or 'opencode run' in line:
                            continue
                        lines.append(line)

                    # Take last 20 useful lines
                    if lines:
                        data["summary"] = '\n'.join(lines[-20:])[:4000]

            _write_yaml(job_file, data)

        # Cleanup
        prompt_file = Path(f"/tmp/listen-codex-prompt-{job_id}.md")
        output_file = Path(f"/tmp/listen-codex-output-{job_id}.txt")
        prompt_file.unlink(missing_ok=True)
        output_file.unlink(missing_ok=True)
        if _session_exists(session_name):
            _tmux("kill-session", "-t", session_name, check=False)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("Usage: worker.py <job_id> <prompt> <agent> [model]")
    job_id = sys.argv[1]
    prompt = sys.argv[2]
    agent = sys.argv[3] if len(sys.argv) > 3 else "codex"
    model = sys.argv[4] if len(sys.argv) > 4 else ""
    # Debug: log received args
    import os
    debug_log = Path("/tmp/worker-debug.log")
    with open(debug_log, "a") as f:
        f.write(f"[{job_id}] agent={agent}, prompt={prompt}, model={model}\n")
    main(job_id, prompt, agent, model)
