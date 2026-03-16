from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from PIL import Image

from rpi_gui.cli import cli


def test_see_command_saves_screenshot(monkeypatch, tmp_path: Path):
    out_file = tmp_path / "shot.png"

    monkeypatch.setattr("rpi_gui.commands.see.capture_screenshot", lambda: Image.new("RGB", (50, 20), "white"))

    result = CliRunner().invoke(cli, ["see", "--output", str(out_file)])
    assert result.exit_code == 0, result.output

    payload = json.loads(result.output)
    assert payload["screenshot"] == str(out_file)
    assert out_file.exists()


def test_see_with_ocr(monkeypatch, tmp_path: Path):
    out_file = tmp_path / "shot.png"
    monkeypatch.setattr("rpi_gui.commands.see.capture_screenshot", lambda: Image.new("RGB", (10, 10), "white"))

    class DummyWord:
        text = "Hello"
        x = 1
        y = 2
        width = 3
        height = 4
        confidence = 99.0

    class DummyOCR:
        text = "Hello"
        words = [DummyWord()]

    monkeypatch.setattr("rpi_gui.commands.see.run_ocr", lambda img: DummyOCR())

    result = CliRunner().invoke(cli, ["see", "--ocr", "--output", str(out_file)])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["text"] == "Hello"
    assert len(payload["elements"]) == 1


def test_ocr_command_writes_json(monkeypatch, tmp_path: Path):
    out_file = tmp_path / "ocr.json"
    monkeypatch.setattr("rpi_gui.commands.ocr.capture_screenshot", lambda: Image.new("RGB", (10, 10), "white"))

    class DummyWord:
        text = "OK"
        x = 0
        y = 0
        width = 5
        height = 8
        confidence = 95.0

    class DummyOCR:
        text = "OK"
        words = [DummyWord()]

    monkeypatch.setattr("rpi_gui.commands.ocr.run_ocr", lambda image, min_confidence=0.0: DummyOCR())

    result = CliRunner().invoke(cli, ["ocr", "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    saved = json.loads(out_file.read_text(encoding="utf-8"))
    assert saved["text"] == "OK"


def test_click_by_coordinates(monkeypatch):
    called = {}

    def fake_click(x, y, button="left", clicks=1, interval=0.0):
        called.update({"x": x, "y": y, "button": button})

    monkeypatch.setattr("rpi_gui.commands.click.click_at", fake_click)

    result = CliRunner().invoke(cli, ["click", "--x", "12", "--y", "34", "--button", "right"])
    assert result.exit_code == 0
    assert called == {"x": 12, "y": 34, "button": "right"}


def test_click_by_text(monkeypatch):
    monkeypatch.setattr("rpi_gui.commands.click.capture_screenshot", lambda: Image.new("RGB", (10, 10), "white"))
    monkeypatch.setattr("rpi_gui.commands.click.find_text_center", lambda image, needle: (55, 66))

    called = {}

    def fake_click(x, y, button="left", clicks=1, interval=0.0):
        called.update({"x": x, "y": y})

    monkeypatch.setattr("rpi_gui.commands.click.click_at", fake_click)

    result = CliRunner().invoke(cli, ["click", "--text", "Submit"])
    assert result.exit_code == 0
    assert called == {"x": 55, "y": 66}


def test_click_requires_target():
    result = CliRunner().invoke(cli, ["click"])
    assert result.exit_code != 0
    assert "Provide --x and --y, or use --text." in result.output


def test_type_command(monkeypatch):
    called = {}

    def fake_type(text, interval=0.0, press_enter=False):
        called.update({"text": text, "interval": interval, "enter": press_enter})

    monkeypatch.setattr("rpi_gui.commands.type.type_text", fake_type)

    result = CliRunner().invoke(cli, ["type", "hello", "--interval", "0.01", "--enter"])
    assert result.exit_code == 0
    assert called["text"] == "hello"
    assert called["enter"] is True
