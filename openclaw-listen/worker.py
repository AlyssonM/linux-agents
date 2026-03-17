from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
REPO_ROOT = BASE_DIR.parent
ACP_RUNNER = BASE_DIR / "acp_runner.mjs"
NODE_BIN = "/usr/bin/node"

_CHILD: subprocess.Popen[str] | None = None
_CANCELLED = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_job(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _append_update(data: dict, text: str) -> None:
    data.setdefault("updates", []).append(text)
    data["updated_at"] = _now()


def _session_key_for_job(job_id: str) -> str:
    return f"agent:listen-v2:job:{job_id}"


def _on_signal(signum, frame):  # noqa: ARG001
    global _CANCELLED
    _CANCELLED = True
    if _CHILD and _CHILD.poll() is None:
        _CHILD.terminate()


def _build_runner_cmd(job: dict, job_id: str) -> list[str]:
    execution = job.get("execution") or {}
    instruction = job.get("instruction") or ""
    timeout_seconds = int(execution.get("timeout_seconds") or 900)
    thinking = execution.get("thinking")
    cmd = [
        NODE_BIN,
        str(ACP_RUNNER),
        "--instruction",
        instruction,
        "--cwd",
        str(REPO_ROOT),
        "--session-key",
        _session_key_for_job(job_id),
        "--timeout-ms",
        str(timeout_seconds * 1000),
    ]
    if thinking:
        cmd += ["--thinking", thinking]
    return cmd


def _parse_runner_output(stdout: str, stderr: str) -> tuple[str, dict]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(stderr.strip() or "ACP runner returned no output")
    last = lines[-1]
    data = json.loads(last)
    message = (data.get("message") or "").strip() if isinstance(data, dict) else ""
    return message, data


def main(job_id: str) -> None:
    global _CHILD
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise SystemExit(f"Job not found: {job_file}")

    job = _read_job(job_file)
    strategy = ((job.get("execution") or {}).get("strategy")) or "auto"
    resolved_strategy = "acp"
    job.setdefault("execution", {})["resolved_strategy"] = resolved_strategy
    job.setdefault("runtime", {})["session_key"] = _session_key_for_job(job_id)
    _append_update(job, f"Execution strategy resolved to: {resolved_strategy}")
    job["status"] = "running"
    _write_job(job_file, job)

    cmd = _build_runner_cmd(job, job_id)
    _append_update(job, "Dispatching job to OpenClaw ACP runtime")
    _write_job(job_file, job)

    try:
        _CHILD = subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = _CHILD.communicate()
    except Exception as exc:
        job = _read_job(job_file)
        job["status"] = "failed"
        job["error"] = {"message": str(exc)}
        _append_update(job, f"Runner spawn failed: {exc}")
        _write_job(job_file, job)
        return

    job = _read_job(job_file)
    job.setdefault("result", {})

    if _CANCELLED:
        job["status"] = "cancelled"
        job["error"] = {"message": "Job cancelled"}
        _append_update(job, "ACP worker cancelled")
        _write_job(job_file, job)
        return

    if _CHILD.returncode == 0:
        try:
            message, payload = _parse_runner_output(stdout, stderr)
            job["status"] = "succeeded"
            job["result"]["summary"] = message[:4000]
            job["result"]["message"] = message
            job["result"]["stop_reason"] = payload.get("stopReason")
            job["runtime"]["session_id"] = payload.get("sessionId")
            job["runtime"]["session_key"] = payload.get("sessionKey") or job["runtime"].get("session_key")
            job["runtime"]["tool_events"] = payload.get("toolEvents", 0)
            if payload.get("updates"):
                job["runtime"]["acp_updates"] = payload.get("updates")
            _append_update(job, "OpenClaw ACP runtime completed successfully")
        except Exception as exc:
            job["status"] = "failed"
            job["error"] = {"message": f"Failed to parse ACP runner output: {exc}"}
            job["result"]["stderr"] = stderr.strip()[:4000]
            _append_update(job, "ACP runtime returned unparseable output")
    else:
        job["status"] = "failed"
        err_message = stderr.strip() or stdout.strip() or f"ACP runner exited with code {_CHILD.returncode}"
        job["error"] = {"message": err_message[:4000]}
        job["result"]["stderr"] = stderr.strip()[:4000]
        _append_update(job, "OpenClaw ACP runtime failed")

    job["result"]["exit_code"] = _CHILD.returncode
    job["updated_at"] = _now()
    _write_job(job_file, job)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: worker.py <job_id>")
    main(sys.argv[1])
