from click.testing import CliRunner
from rpi_term.cli import cli


def test_run_command(monkeypatch):
    monkeypatch.setattr("rpi_term.modules.sentinel.run_and_wait", lambda *a, **k: (0, "ok"))
    result = CliRunner().invoke(cli, ["run", "--session", "s1", "echo hi"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_session_create(monkeypatch):
    monkeypatch.setattr("rpi_term.modules.tmux.create_session", lambda *a, **k: None)
    result = CliRunner().invoke(cli, ["session", "create", "--name", "agent-1"])
    assert result.exit_code == 0
    assert "Created session: agent-1" in result.output
