from pathlib import Path
from fastapi.testclient import TestClient
import yaml

from rpi_job import main


def test_job_lifecycle(tmp_path, monkeypatch):
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    monkeypatch.setattr(main, "JOBS_DIR", jobs)
    monkeypatch.setattr(main, "ARCHIVED_DIR", jobs / "archived")

    class DummyProc:
        pid = 12345

    monkeypatch.setattr(main.subprocess, "Popen", lambda *a, **k: DummyProc())

    client = TestClient(main.app)

    r = client.post("/job", json={"prompt": "hello"})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    r2 = client.get(f"/job/{job_id}")
    assert r2.status_code == 200
    data = yaml.safe_load(r2.text)
    assert data["prompt"] == "hello"

    r3 = client.get("/jobs")
    assert "jobs:" in r3.text

    r4 = client.delete(f"/job/{job_id}")
    assert r4.status_code == 200
    assert r4.json()["status"] == "stopped"
