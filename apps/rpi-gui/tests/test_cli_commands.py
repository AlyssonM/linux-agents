from click.testing import CliRunner

from rpi_gui.cli import cli


def test_hotkey_command(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.hotkey.run_hotkey", lambda keys: None)
    runner = CliRunner()
    result = runner.invoke(cli, ["hotkey", "ctrl+s"])
    assert result.exit_code == 0
    assert "hotkey sent" in result.output


def test_scroll_command(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.scroll.run_scroll", lambda direction, steps, clicks_per_step: 360)
    runner = CliRunner()
    result = runner.invoke(cli, ["scroll", "up", "3"])
    assert result.exit_code == 0
    assert "scrolled up" in result.output


def test_drag_command(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.drag.run_drag", lambda **kwargs: None)
    runner = CliRunner()
    result = runner.invoke(cli, ["drag", "--from", "10,20", "--to", "50,60"])
    assert result.exit_code == 0
    assert "drag complete" in result.output


def test_focus_command(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.focus.focus_window", lambda query, exact=False: "99")
    runner = CliRunner()
    result = runner.invoke(cli, ["focus", "Firefox"])
    assert result.exit_code == 0
    assert "focused window 99" in result.output


def test_drag_invalid_point():
    runner = CliRunner()
    result = runner.invoke(cli, ["drag", "--from", "10x20", "--to", "50,60"])
    assert result.exit_code != 0
    assert "expected format x,y" in result.output
