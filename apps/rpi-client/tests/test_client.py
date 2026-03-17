from rpi_client import client


class Resp:
    def __init__(self, text="", js=None):
        self.text = text
        self._js = js or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._js


def test_start_job(monkeypatch):
    monkeypatch.setattr(client.httpx, "request", lambda *a, **k: Resp(js={"job_id": "abc"}))
    assert client.start_job("http://x", "do it")["job_id"] == "abc"


def test_latest_jobs(monkeypatch):
    monkeypatch.setattr(client, "list_jobs", lambda url, archived=False: "jobs:\n- id: j1\n- id: j2\n")
    monkeypatch.setattr(client, "get_job", lambda url, job_id: f"id: {job_id}")
    out = client.latest_jobs("http://x", 1)
    assert "id: j2" in out
