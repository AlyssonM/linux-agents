from __future__ import annotations

import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
REPO_ROOT = BASE_DIR.parent.parent
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


def _run_subagent(job: dict, job_id: str) -> dict:
    """Execute job using inline Python (subagent subprocess)."""
    import time

    instruction = job.get("instruction") or ""
    execution = job.get("execution") or {}
    timeout_seconds = int(execution.get("timeout_seconds") or 900)

    _append_update(job, "Running job with subagent")

    # Build inline subagent script that calls OpenClaw agent
    # Note: model is configured in the agent, not via CLI flag
    subagent_script = f"""#!/usr/bin/env python3
import sys
import subprocess

instruction = '''{instruction}'''

# Call OpenClaw agent with the instruction
cmd = [
    "/usr/bin/node",
    "/home/alyssonpi/.npm-global/lib/node_modules/openclaw/openclaw.mjs",
    "agent",
    "--agent", "main",
    "--message", instruction,
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout={timeout_seconds})

if result.returncode == 0:
    print(result.stdout)
    sys.exit(0)
else:
    print(f"Error: {{result.stderr}}", file=sys.stderr)
    sys.exit(result.returncode)
"""

    # Write temporary script
    script_path = BASE_DIR / f"_{job_id}_subagent.py"
    script_path.write_text(subagent_script)

    _append_update(job, f"Executing subagent: {script_path.name}")

    start_time = time.time()
    child = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        stdout, stderr = child.communicate(timeout=timeout_seconds)
        elapsed = time.time() - start_time

        # Cleanup
        script_path.unlink(missing_ok=True)

        if child.returncode == 0:
            job["status"] = "succeeded"
            job["result"] = {
                "summary": stdout.strip()[:4000],
                "message": stdout.strip(),
                "exit_code": 0,
            }
            job.setdefault("runtime", {})["elapsed_seconds"] = round(elapsed, 2)
            _append_update(job, f"Subagent completed in {elapsed:.1f}s")
        else:
            job["status"] = "failed"
            job["error"] = {
                "message": stderr.strip()[:4000] or f"Subagent exited with code {child.returncode}",
            }
            job["result"] = {
                "exit_code": child.returncode,
                "stderr": stderr.strip()[:4000],
                "stdout": stdout.strip()[:4000],
            }
            _append_update(job, f"Subagent failed with code {child.returncode}")

    except subprocess.TimeoutExpired:
        child.kill()
        script_path.unlink(missing_ok=True)
        job["status"] = "failed"
        job["error"] = {"message": f"Subagent timed out after {timeout_seconds}s"}
        _append_update(job, f"Subagent timed out after {timeout_seconds}s")

    return job


def main(job_id: str) -> None:
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise SystemExit(f"Job not found: {job_file}")

    job = _read_job(job_file)
    strategy = ((job.get("execution") or {}).get("strategy")) or "auto"

    # All strategies resolve to subagent
    resolved_strategy = "subagent"

    job.setdefault("execution", {})["resolved_strategy"] = resolved_strategy
    job.setdefault("runtime", {})["session_key"] = _session_key_for_job(job_id)
    _append_update(job, f"Execution strategy resolved to: {resolved_strategy}")
    job["status"] = "running"
    _write_job(job_file, job)

    # Execute with subagent
    job = _run_subagent(job, job_id)
    _write_job(job_file, job)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: worker.py <job_id>")
    main(sys.argv[1])
