from __future__ import annotations

import json
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
_CURRENT_PROC: subprocess.Popen[str] | None = None
_CANCEL_REQUESTED = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_job(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _append_update(data: dict, text: str) -> None:
    data.setdefault("updates", []).append(text)
    data["updated_at"] = _now()


def _handle_signal(signum: int, _frame) -> None:
    global _CANCEL_REQUESTED
    _CANCEL_REQUESTED = True
    if _CURRENT_PROC and _CURRENT_PROC.poll() is None:
        _CURRENT_PROC.terminate()


for _sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(_sig, _handle_signal)


def _build_openclaw_cmd(job: dict) -> list[str]:
    execution = job.get("execution") or {}
    delivery = job.get("delivery") or {}
    instruction = job.get("instruction") or ""
    thinking = execution.get("thinking")
    agent = execution.get("agent")

    cmd = ["openclaw", "agent", "--local", "--json", "--message", instruction]
    timeout_seconds = execution.get("timeout_seconds")
    if timeout_seconds:
        cmd += ["--timeout", str(timeout_seconds)]
    if thinking:
        cmd += ["--thinking", thinking]
    if agent:
        cmd += ["--agent", agent]

    if delivery.get("send_result"):
        cmd += ["--deliver"]
        if delivery.get("channel"):
            cmd += ["--reply-channel", delivery["channel"]]
        if delivery.get("target"):
            cmd += ["--reply-to", delivery["target"]]
    return cmd


def _extract_result(stdout: str) -> tuple[str, str]:
    text = stdout.strip()
    if not text:
        return "", ""
    lines = [line for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                if "message" in payload and isinstance(payload["message"], str):
                    msg = payload["message"].strip()
                    return msg[:4000], msg
                if "output" in payload and isinstance(payload["output"], str):
                    msg = payload["output"].strip()
                    return msg[:4000], msg
        except json.JSONDecodeError:
            continue
    return text[:4000], text


def main(job_id: str) -> None:
    global _CURRENT_PROC

    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise SystemExit(f"Job not found: {job_file}")

    job = _read_job(job_file)
    strategy = ((job.get("execution") or {}).get("resolved_strategy")) or "inline"

    if strategy == "acp":
        job["status"] = "failed"
        job["error"] = {"message": "ACP strategy not implemented in openclaw-listen v1"}
        _append_update(job, "ACP strategy requested but not implemented in v1")
        _write_job(job_file, job)
        return

    _append_update(job, f"Execution strategy resolved to: {strategy}")
    job["status"] = "running"
    _write_job(job_file, job)

    cmd = _build_openclaw_cmd(job)
    _append_update(job, "Dispatching job to local OpenClaw runtime")
    _write_job(job_file, job)

    _CURRENT_PROC = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = _CURRENT_PROC.communicate()
    returncode = _CURRENT_PROC.returncode

    job = _read_job(job_file)
    summary, full_message = _extract_result(stdout)
    job.setdefault("result", {})
    job["result"]["summary"] = summary
    job["result"]["message"] = full_message
    job["result"]["exit_code"] = returncode
    if stderr.strip():
        job["result"]["stderr"] = stderr.strip()[:4000]

    if _CANCEL_REQUESTED:
        job["status"] = "cancelled"
        job["error"] = None
        _append_update(job, "Cancellation requested")
    elif returncode == 0:
        job["status"] = "succeeded"
        _append_update(job, "OpenClaw runtime completed successfully")
    else:
        job["status"] = "failed"
        job["error"] = {"message": stderr.strip() or f"openclaw agent exited with code {returncode}"}
        _append_update(job, "OpenClaw runtime failed")

    job["updated_at"] = _now()
    _write_job(job_file, job)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: worker.py <job_id>")
    main(sys.argv[1])
