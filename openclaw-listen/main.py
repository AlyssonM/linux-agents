from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

app = FastAPI(title="openclaw-listen")
BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
ARCHIVED_DIR = JOBS_DIR / "archived"
JOBS_DIR.mkdir(exist_ok=True)
ARCHIVED_DIR.mkdir(exist_ok=True)


class Source(BaseModel):
    type: Literal["rest", "direct", "telegram", "discord", "gateway"] = "rest"
    channel: str | None = None
    chat_id: str | None = None
    message_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None


class Delivery(BaseModel):
    mode: Literal["poll", "reply", "push"] = "poll"
    send_result: bool = False
    channel: str | None = None
    target: str | None = None
    reply_to: str | None = None
    thread_id: str | None = None
    format_style: Literal["compact", "normal"] = "compact"


class Execution(BaseModel):
    strategy: Literal["auto", "inline", "subagent", "acp"] = "auto"
    timeout_seconds: int = Field(default=900, ge=30, le=7200)
    thinking: Literal["off", "minimal", "low", "medium", "high", "xhigh"] | None = None
    agent: str | None = None


class JobRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=16000)
    source: Source = Field(default_factory=Source)
    delivery: Delivery = Field(default_factory=Delivery)
    execution: Execution = Field(default_factory=Execution)
    input: dict = Field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_job(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


@app.post("/jobs")
def create_job(req: JobRequest):
    job_id = uuid4().hex[:8]
    job_file = JOBS_DIR / f"{job_id}.yaml"
    requested_strategy = req.execution.strategy
    resolved_strategy = "inline" if requested_strategy in {"auto", "subagent"} else requested_strategy

    data = {
        "id": job_id,
        "kind": "task",
        "status": "queued",
        "created_at": _now(),
        "updated_at": _now(),
        "instruction": req.instruction,
        "source": req.source.model_dump(),
        "delivery": req.delivery.model_dump(),
        "execution": {
            **req.execution.model_dump(),
            "resolved_strategy": resolved_strategy,
        },
        "input": req.input,
        "runtime": {
            "pid": 0,
            "worker": "openclaw-listen/worker.py",
        },
        "updates": [],
        "artifacts": [],
        "result": {
            "summary": "",
            "message": "",
        },
        "error": None,
    }
    _write_job(job_file, data)

    worker_path = BASE_DIR / "worker.py"
    try:
        proc = subprocess.Popen(
            [sys.executable, str(worker_path), job_id],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        data["status"] = "failed"
        data["updated_at"] = _now()
        data["error"] = {"message": str(exc)}
        data["updates"].append("Failed to spawn worker")
        _write_job(job_file, data)
        raise HTTPException(status_code=500, detail="Failed to start worker process") from exc

    data = _read_job(job_file)
    data["runtime"]["pid"] = proc.pid
    data["status"] = "planning"
    data["updated_at"] = _now()
    data["updates"].append("Job accepted and worker spawned")
    _write_job(job_file, data)
    return JSONResponse({"id": job_id, "job_id": job_id, "status": data["status"], "status_url": f"/jobs/{job_id}"}, status_code=202)


@app.get("/jobs/{job_id}", response_class=PlainTextResponse)
def get_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    return job_file.read_text(encoding="utf-8")


@app.get("/jobs", response_class=PlainTextResponse)
def list_jobs(archived: bool = False, status: str | None = None, source_type: str | None = None):
    search_dir = ARCHIVED_DIR if archived else JOBS_DIR
    search_dir.mkdir(exist_ok=True)
    jobs = []
    for f in sorted(search_dir.glob("*.yaml")):
        data = _read_job(f)
        row = {
            "id": data.get("id"),
            "status": data.get("status"),
            "instruction": data.get("instruction"),
            "source_type": (data.get("source") or {}).get("type"),
            "strategy": ((data.get("execution") or {}).get("resolved_strategy")),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }
        if status and row["status"] != status:
            continue
        if source_type and row["source_type"] != source_type:
            continue
        jobs.append(row)
    jobs_sorted = sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)
    return yaml.dump({"jobs": jobs_sorted}, default_flow_style=False, sort_keys=False)


@app.post("/jobs/clear")
def clear_jobs():
    count = 0
    for f in JOBS_DIR.glob("*.yaml"):
        shutil.move(str(f), str(ARCHIVED_DIR / f.name))
        count += 1
    return {"archived": count}


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    data = _read_job(job_file)
    pid = (data.get("runtime") or {}).get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    data["status"] = "cancelled"
    data["updated_at"] = _now()
    data.setdefault("updates", []).append("Cancellation requested")
    _write_job(job_file, data)
    return {"job_id": job_id, "status": "cancelled"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7610)
