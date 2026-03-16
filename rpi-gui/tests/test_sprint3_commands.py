from __future__ import annotations

import json

from click.testing import CliRunner

from rpi_gui.cli import cli


def test_apps_list_command(monkeypatch):
    monkeypatch.setattr(
        "rpi_gui.commands.apps.list_running_apps",
        lambda: [{"name": "Chromium", "role": "application"}],
    )
    res = CliRunner().invoke(cli, ["apps", "list"])
    assert res.exit_code == 0, res.output
    data = json.loads(res.output)
    assert data["apps"][0]["name"] == "Chromium"


def test_screens_list_command(monkeypatch):
    monkeypatch.setattr(
        "rpi_gui.commands.screens.list_screens",
        lambda: [{"index": 0, "name": "HDMI-1", "x": 0, "y": 0, "width": 1920, "height": 1080}],
    )
    res = CliRunner().invoke(cli, ["screens", "list"])
    assert res.exit_code == 0
    assert "HDMI-1" in res.output


def test_window_move_command(monkeypatch):
    monkeypatch.setattr(
        "rpi_gui.commands.window.move_window",
        lambda **kwargs: {"ok": True, "action": "move", **kwargs},
    )
    res = CliRunner().invoke(
        cli,
        ["window", "move", "--target", "Chromium", "--x", "10", "--y", "20"],
    )
    assert res.exit_code == 0
    out = json.loads(res.output)
    assert out["action"] == "move"


def test_find_command_requires_filters():
    res = CliRunner().invoke(cli, ["find"])
    assert res.exit_code != 0
    assert "Provide at least one filter" in res.output


def test_find_command_success(monkeypatch):
    monkeypatch.setattr(
        "rpi_gui.commands.find.find_elements",
        lambda **kwargs: [{"name": "Settings", "role": "push button", "app": "Chromium", "states": []}],
    )
    res = CliRunner().invoke(cli, ["find", "--text", "Settings"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["count"] == 1
