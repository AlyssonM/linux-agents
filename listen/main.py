from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="listen")
BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
ARCHIVED_DIR = JOBS_DIR / "archived"
JOBS_DIR.mkdir(exist_ok=True)
ARCHIVED_DIR.mkdir(exist_ok=True)


class JobRequest(BaseModel):
    prompt: str
    agent: str = "codex"  # codex, claude, openclaw, opencode, pi
    model: str | None = None
    timeout_seconds: int = 900


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _read_job(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@app.post("/job")
def create_job(req: JobRequest):
    job_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    job_file = JOBS_DIR / f"{job_id}.yaml"

    data = {
        "id": job_id,
        "status": "running",
        "prompt": req.prompt,
        "agent": req.agent or "codex",
        "model": req.model,
        "created_at": now,
        "pid": 0,
        "session": "",
        "updates": [],
        "summary": "",
    }
    _write_job(job_file, data)

    worker_path = BASE_DIR / "worker.py"
    proc = subprocess.Popen(
        [sys.executable, str(worker_path), job_id, req.prompt, req.agent, req.model or ""],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    data["pid"] = proc.pid
    _write_job(job_file, data)
    return {"job_id": job_id, "status": "running"}


@app.get("/job/{job_id}", response_class=PlainTextResponse)
def get_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    return job_file.read_text(encoding="utf-8")


@app.get("/jobs", response_class=PlainTextResponse)
def list_jobs(archived: bool = False):
    search_dir = ARCHIVED_DIR if archived else JOBS_DIR
    jobs = []
    for f in sorted(search_dir.glob("*.yaml")):
        data = _read_job(f)
        jobs.append(
            {
                "id": data.get("id"),
                "status": data.get("status"),
                "prompt": data.get("prompt"),
                "created_at": data.get("created_at"),
                "completed_at": data.get("completed_at"),
            }
        )
    return yaml.dump({"jobs": jobs}, default_flow_style=False, sort_keys=False)


@app.post("/jobs/clear")
def clear_jobs():
    count = 0
    for f in JOBS_DIR.glob("*.yaml"):
        shutil.move(str(f), str(ARCHIVED_DIR / f.name))
        count += 1
    return {"archived": count}


@app.delete("/job/{job_id}")
def stop_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    data = _read_job(job_file)
    pid = data.get("pid")
    session = data.get("session")

    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    if session:
        subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True, text=True)

    data["status"] = "stopped"
    _write_job(job_file, data)
    return {"job_id": job_id, "status": "stopped"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7600)
