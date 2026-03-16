import subprocess

import pytest

from rpi_gui.modules import input as input_mod


def test_run_hotkey_normalizes_aliases(monkeypatch):
    sent = {}

    def fake_hotkey(*keys):
        sent["keys"] = keys

    monkeypatch.setattr("pyautogui.hotkey", fake_hotkey)
    input_mod.run_hotkey(["CTRL", "s"])
    assert sent["keys"] == ("ctrl", "s")


def test_run_hotkey_empty_raises():
    with pytest.raises(ValueError):
        input_mod.run_hotkey([])


def test_scroll_up(monkeypatch):
    calls = []
    monkeypatch.setattr("pyautogui.scroll", lambda amount: calls.append(amount))
    amount = input_mod.run_scroll("up", 3, clicks_per_step=10)
    assert amount == 30
    assert calls == [30]


def test_scroll_down(monkeypatch):
    calls = []
    monkeypatch.setattr("pyautogui.scroll", lambda amount: calls.append(amount))
    amount = input_mod.run_scroll("down", 2, clicks_per_step=10)
    assert amount == -20
    assert calls == [-20]


def test_run_drag(monkeypatch):
    moved = []
    dragged = []
    monkeypatch.setattr("pyautogui.moveTo", lambda x, y: moved.append((x, y)))
    monkeypatch.setattr(
        "pyautogui.dragTo",
        lambda x, y, duration, button: dragged.append((x, y, duration, button)),
    )
    input_mod.run_drag(1, 2, 3, 4, duration=0.5, button="left")
    assert moved == [(1, 2)]
    assert dragged == [(3, 4, 0.5, "left")]


def test_focus_window_success(monkeypatch):
    monkeypatch.setattr(input_mod.shutil, "which", lambda _x: "/usr/bin/xdotool")
    responses = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout="123\n", stderr=""),
        subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
    ]

    def fake_run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(input_mod.subprocess, "run", fake_run)
    assert input_mod.focus_window("Firefox") == "123"


def test_focus_window_no_xdotool(monkeypatch):
    monkeypatch.setattr(input_mod.shutil, "which", lambda _x: None)
    with pytest.raises(RuntimeError, match="xdotool not found"):
        input_mod.focus_window("Firefox")
