from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="listen")
BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
ARCHIVED_DIR = JOBS_DIR / "archived"
UPLOADS_DIR = JOBS_DIR / "uploads"
JOBS_DIR.mkdir(exist_ok=True)
ARCHIVED_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


class JobRequest(BaseModel):
    prompt: str
    agent: str = "codex"  # codex, claude, openclaw, opencode, pi
    model: str | None = None
    timeout_seconds: int = 900
    api_key: str | None = None
    api_key_env: str | None = None
    lmstudio_base_url: str | None = None
    image_attachments: list[str] | None = None


def _infer_api_key_env(model: str | None) -> str | None:
    if not model:
        return None
    provider = model.split("/", 1)[0].split(":", 1)[0].strip()
    if not provider:
        return None
    provider = re.sub(r"[^A-Za-z0-9]", "_", provider).upper()
    return f"{provider}_API_KEY"


def _write_job(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")


def _read_job(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _normalize_image_attachments(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        item = value.strip()
        if item and item not in normalized:
            normalized.append(item)
    return normalized


def _safe_filename(name: str, index: int) -> str:
    candidate = Path(name).name
    if not candidate:
        candidate = f"image_{index}.bin"
    candidate = re.sub(r"[^A-Za-z0-9._-]", "_", candidate)
    if not candidate:
        candidate = f"image_{index}.bin"
    return candidate


def _prepare_job_payload(
    job_id: str,
    prompt: str,
    agent: str,
    model: str | None,
    image_attachments: list[str],
) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": job_id,
        "status": "running",
        "prompt": prompt,
        "agent": agent or "codex",
        "model": model,
        "image_attachments": image_attachments,
        "created_at": now,
        "pid": 0,
        "session": "",
        "updates": [],
        "summary": "",
    }


def _spawn_job_worker(
    job_id: str,
    prompt: str,
    agent: str,
    model: str | None,
    api_key: str | None,
    api_key_env: str | None,
    lmstudio_base_url: str | None,
) -> int:
    worker_path = BASE_DIR / "worker.py"
    env = os.environ.copy()
    for key in ("LMSTUDIO_BASE_URL", "LMSTUDIO_API_KEY", "LMSTUDIO_EXTENSION_PATH"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    if lmstudio_base_url:
        env["LMSTUDIO_BASE_URL"] = lmstudio_base_url
    inferred_env = api_key_env or _infer_api_key_env(model)
    if inferred_env:
        env["LISTEN_API_KEY_ENV"] = inferred_env
    if api_key:
        if inferred_env:
            env["LISTEN_API_KEY"] = api_key
    proc = subprocess.Popen(
        [sys.executable, str(worker_path), job_id, prompt, agent, model or ""],
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.pid


async def _store_uploaded_images(job_id: str, image_files: list[UploadFile]) -> list[str]:
    if not image_files:
        return []
    upload_dir = UPLOADS_DIR / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []
    for index, image_file in enumerate(image_files, start=1):
        if image_file.content_type and not image_file.content_type.lower().startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {image_file.filename}")
        safe_name = _safe_filename(image_file.filename or "", index)
        target = upload_dir / safe_name
        payload = await image_file.read()
        target.write_bytes(payload)
        saved_paths.append(str(target))
    return saved_paths


@app.post("/job")
def create_job(req: JobRequest):
    job_id = uuid4().hex[:8]
    job_file = JOBS_DIR / f"{job_id}.yaml"
    image_attachments = _normalize_image_attachments(req.image_attachments)
    data = _prepare_job_payload(job_id, req.prompt, req.agent, req.model, image_attachments)
    _write_job(job_file, data)
    data["pid"] = _spawn_job_worker(
        job_id,
        req.prompt,
        req.agent,
        req.model,
        req.api_key,
        req.api_key_env,
        req.lmstudio_base_url,
    )
    _write_job(job_file, data)
    return {"job_id": job_id, "status": "running"}


@app.post("/job/upload")
async def create_job_with_upload(
    prompt: str = Form(...),
    agent: str = Form("codex"),
    model: str | None = Form(None),
    timeout_seconds: int = Form(900),
    api_key: str | None = Form(None),
    api_key_env: str | None = Form(None),
    lmstudio_base_url: str | None = Form(None),
    image_attachments: list[str] | None = Form(None),
    image_files: list[UploadFile] = File(default_factory=list),
):
    _ = timeout_seconds
    job_id = uuid4().hex[:8]
    job_file = JOBS_DIR / f"{job_id}.yaml"
    uploaded_paths = await _store_uploaded_images(job_id, image_files)
    attachments = _normalize_image_attachments((image_attachments or []) + uploaded_paths)
    data = _prepare_job_payload(job_id, prompt, agent, model, attachments)
    _write_job(job_file, data)
    data["pid"] = _spawn_job_worker(job_id, prompt, agent, model, api_key, api_key_env, lmstudio_base_url)
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
