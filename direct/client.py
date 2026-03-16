from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx
import yaml

logger = logging.getLogger(__name__)


class ClientError(RuntimeError):
    pass


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ClientError(f"Invalid server URL: {url}")
    return url.rstrip("/")


def _request_json(method: str, url: str, **kwargs) -> dict:
    try:
        response = httpx.request(method, url, timeout=10.0, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        logger.error("HTTP error on %s %s: %s", method, url, exc)
        raise ClientError(f"Request failed: {exc}") from exc


def _request_text(method: str, url: str, **kwargs) -> str:
    try:
        response = httpx.request(method, url, timeout=10.0, **kwargs)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as exc:
        logger.error("HTTP error on %s %s: %s", method, url, exc)
        raise ClientError(f"Request failed: {exc}") from exc


def start_job(url: str, prompt: str) -> dict:
    base = _validate_url(url)
    if not prompt.strip():
        raise ClientError("Prompt cannot be empty or whitespace-only")
    return _request_json("POST", f"{base}/job", json={"prompt": prompt})


def get_job(url: str, job_id: str) -> str:
    base = _validate_url(url)
    if not job_id.strip():
        raise ClientError("job_id cannot be empty")
    return _request_text("GET", f"{base}/job/{job_id}")


def list_jobs(url: str, archived: bool = False) -> str:
    base = _validate_url(url)
    params = {"archived": "true"} if archived else {}
    return _request_text("GET", f"{base}/jobs", params=params)


def clear_jobs(url: str) -> dict:
    base = _validate_url(url)
    return _request_json("POST", f"{base}/jobs/clear")


def stop_job(url: str, job_id: str) -> dict:
    base = _validate_url(url)
    if not job_id.strip():
        raise ClientError("job_id cannot be empty")
    return _request_json("DELETE", f"{base}/job/{job_id}")


def latest_jobs(url: str, n: int = 1) -> str:
    if n < 1:
        raise ClientError("n must be >= 1")
    data = yaml.safe_load(list_jobs(url)) or {}
    jobs = data.get("jobs") or []
    jobs_sorted = sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)
    return "---\n".join(get_job(url, j["id"]) for j in jobs_sorted[:n] if "id" in j)
