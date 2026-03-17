from click.testing import CliRunner

from rpi_client.main import cli


def test_cli_latest(monkeypatch):
    monkeypatch.setattr("rpi_client.client.latest_jobs", lambda url, n=1: "id: j1")
    out = CliRunner().invoke(cli, ["latest", "http://x", "-n", "1"])
    assert out.exit_code == 0
    assert "id: j1" in out.output
