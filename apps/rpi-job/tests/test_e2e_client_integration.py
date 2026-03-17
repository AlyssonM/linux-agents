from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rpi-client"))
from rpi_client import client as c
from rpi_job import main


class BridgeResponse:
    def __init__(self, resp):
        self._resp = resp
        self.text = resp.text

    def raise_for_status(self):
        assert self._resp.status_code < 400

    def json(self):
        return self._resp.json()


def test_job_client_flow(tmp_path, monkeypatch):
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    monkeypatch.setattr(main, "JOBS_DIR", jobs)
    monkeypatch.setattr(main, "ARCHIVED_DIR", jobs / "archived")

    class DummyProc:
        pid = 12345

    monkeypatch.setattr(main.subprocess, "Popen", lambda *a, **k: DummyProc())

    api = TestClient(main.app)

    def fake_request(method, url, timeout=10.0, **kwargs):
        path = url.split("http://local", 1)[-1]
        if method == "POST" and path == "/job":
            return BridgeResponse(api.post(path, json=kwargs.get("json")))
        if method == "GET" and path.startswith("/job/"):
            return BridgeResponse(api.get(path))
        if method == "GET" and path.startswith("/jobs"):
            return BridgeResponse(api.get(path, params=kwargs.get("params")))
        if method == "DELETE" and path.startswith("/job/"):
            return BridgeResponse(api.delete(path))
        raise AssertionError(f"unexpected {method} {path}")

    monkeypatch.setattr(c.httpx, "request", fake_request)

    out = c.start_job("http://local", "hello")
    job_id = out["job_id"]
    assert job_id
    assert "hello" in c.get_job("http://local", job_id)
    assert "jobs:" in c.list_jobs("http://local")
