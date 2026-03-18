from __future__ import annotations

import logging
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
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="rpi-job")
BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
ARCHIVED_DIR = JOBS_DIR / "archived"
JOBS_DIR.mkdir(exist_ok=True)


class JobRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


def _job_file(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.yaml"


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


@app.post("/job")
def create_job(req: JobRequest):
    job_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    job_data = {"id": job_id, "status": "running", "prompt": req.prompt, "created_at": now, "pid": 0, "updates": [], "summary": ""}
    path = _job_file(job_id)
    _write_job(path, job_data)

    worker = BASE_DIR / "worker.py"
    try:
        proc = subprocess.Popen(
            [sys.executable, str(worker), job_id, req.prompt],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        logger.exception("Failed to start worker for job %s", job_id)
        job_data["status"] = "failed"
        job_data["summary"] = str(exc)
        _write_job(path, job_data)
        raise HTTPException(500, "Failed to start worker process") from exc

    job_data["pid"] = proc.pid
    _write_job(path, job_data)
    logger.info("Created job %s with pid=%s", job_id, proc.pid)
    return {"job_id": job_id, "status": "running"}


@app.get("/job/{job_id}", response_class=PlainTextResponse)
def get_job(job_id: str):
    path = _job_file(job_id)
    if not path.exists():
        raise HTTPException(404, "Job not found")
    return path.read_text(encoding="utf-8")


@app.get("/jobs", response_class=PlainTextResponse)
def list_jobs(archived: bool = False):
    folder = ARCHIVED_DIR if archived else JOBS_DIR
    folder.mkdir(exist_ok=True)
    rows = []
    for f in sorted(folder.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        rows.append({k: data.get(k) for k in ["id", "status", "prompt", "created_at"]})
    # Sort by created_at descending (newest first)
    rows_sorted = sorted(rows, key=lambda j: j.get("created_at", ""), reverse=True)
    return yaml.dump({"jobs": rows_sorted}, default_flow_style=False, sort_keys=False)


@app.delete("/job/{job_id}")
def stop_job(job_id: str):
    path = _job_file(job_id)
    if not path.exists():
        raise HTTPException(404, "Job not found")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pid = data.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info("Sent SIGTERM to pid=%s for job %s", pid, job_id)
        except ProcessLookupError:
            logger.warning("Job pid %s already exited for job %s", pid, job_id)
    data["status"] = "stopped"
    _write_job(path, data)
    return {"job_id": job_id, "status": "stopped"}


@app.post("/jobs/clear")
def clear_jobs():
    ARCHIVED_DIR.mkdir(exist_ok=True)
    count = 0
    for f in JOBS_DIR.glob("*.yaml"):
        shutil.move(str(f), str(ARCHIVED_DIR / f.name))
        count += 1
    logger.info("Archived %d jobs", count)
    return {"archived": count}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7600)
