from __future__ import annotations

import types

import pytest

from rpi_gui.modules import accessibility as acc


def test_list_screens_from_xrandr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")

    def fake_run(cmd: list[str]):
        return types.SimpleNamespace(
            returncode=0,
            stdout="HDMI-1 connected primary 1920x1080+0+0\nDP-1 disconnected\n",
            stderr="",
        )

    monkeypatch.setattr(acc, "_run", fake_run)
    screens = acc.list_screens()
    assert len(screens) == 1
    assert screens[0]["name"] == "HDMI-1"
    assert screens[0]["width"] == 1920


def test_list_windows_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    line = "0x01e00007  0 0 0 800 600 host chromium.Chromium Chromium"

    def fake_run(cmd: list[str]):
        return types.SimpleNamespace(returncode=0, stdout=line + "\n", stderr="")

    monkeypatch.setattr(acc, "_run", fake_run)
    windows = acc.list_windows()
    assert windows[0]["id"] == "0x01e00007"
    assert windows[0]["title"] == "Chromium"


def test_resolve_window_by_title(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        acc,
        "list_windows",
        lambda: [{"id": "0x1", "title": "Terminal", "wm_class": "xfce4-terminal"}],
    )
    assert acc._resolve_window_id("term") == "0x1"


def test_find_requires_pyatspi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(acc, "_load_pyatspi", lambda: None)
    with pytest.raises(acc.AccessibilityError):
        acc.find_elements(text="Settings")
