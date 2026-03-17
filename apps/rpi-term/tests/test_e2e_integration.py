from click.testing import CliRunner

from rpi_term.cli import cli


def test_term_workflow(monkeypatch):
    monkeypatch.setattr("rpi_term.modules.tmux.create_session", lambda *a, **k: None)
    monkeypatch.setattr("rpi_term.modules.tmux.send_keys", lambda *a, **k: None)
    monkeypatch.setattr("rpi_term.modules.tmux.capture_pane", lambda *a, **k: "ok done")
    monkeypatch.setattr("rpi_term.modules.tmux.kill_session", lambda *a, **k: None)
    monkeypatch.setattr("rpi_term.modules.sentinel.run_and_wait", lambda *a, **k: (0, "ok done"))

    runner = CliRunner()
    assert runner.invoke(cli, ["session", "create", "--name", "agent-1"]).exit_code == 0
    assert runner.invoke(cli, ["send", "--session", "agent-1", "echo hi"]).exit_code == 0
    assert runner.invoke(cli, ["run", "--session", "agent-1", "echo hi"]).exit_code == 0
    assert runner.invoke(cli, ["logs", "--session", "agent-1"]).exit_code == 0
