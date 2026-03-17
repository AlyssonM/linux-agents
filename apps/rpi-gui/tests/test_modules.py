from __future__ import annotations

from PIL import Image
import pytest

from rpi_gui.modules.input import click_at, type_text
from rpi_gui.modules.ocr import find_text_center


def test_find_text_center_found(monkeypatch):
    class DummyWord:
        text = "Settings"
        x = 10
        y = 20
        width = 30
        height = 10
        confidence = 99.0

    class DummyResult:
        text = "Settings"
        words = [DummyWord()]

    monkeypatch.setattr("rpi_gui.modules.ocr.run_ocr", lambda image, min_confidence=0.0: DummyResult())

    x, y = find_text_center(Image.new("RGB", (100, 100)), "sett")
    assert (x, y) == (25, 25)


def test_find_text_center_not_found(monkeypatch):
    class DummyResult:
        text = ""
        words = []

    monkeypatch.setattr("rpi_gui.modules.ocr.run_ocr", lambda image, min_confidence=0.0: DummyResult())

    with pytest.raises(ValueError):
        find_text_center(Image.new("RGB", (100, 100)), "missing")


def test_click_at_invalid_coords():
    with pytest.raises(ValueError):
        click_at(-1, 20)


def test_type_text_none_rejected():
    with pytest.raises(ValueError):
        type_text(None)  # type: ignore[arg-type]
