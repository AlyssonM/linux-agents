from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytesseract
from PIL import Image


class OCRError(RuntimeError):
    pass


@dataclass
class OCRWord:
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class OCRResult:
    text: str
    words: list[OCRWord]


def run_ocr(image: Image.Image, min_confidence: float = 0.0) -> OCRResult:
    try:
        text = pytesseract.image_to_string(image)
        data: dict[str, list[Any]] = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except Exception as exc:
        raise OCRError(f"OCR failed: {exc}") from exc

    words: list[OCRWord] = []
    for i, raw in enumerate(data.get("text", [])):
        token = str(raw).strip()
        if not token:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1
        if conf < min_confidence:
            continue
        words.append(OCRWord(token, int(data["left"][i]), int(data["top"][i]), int(data["width"][i]), int(data["height"][i]), conf))

    return OCRResult(text=text.strip(), words=words)


def find_text_center(image: Image.Image, needle: str, min_confidence: float = 0.0) -> tuple[int, int]:
    needle_norm = needle.strip().lower()
    if not needle_norm:
        raise ValueError("Text to find cannot be empty")

    result = run_ocr(image, min_confidence=min_confidence)
    for word in result.words:
        if needle_norm in word.text.lower():
            return word.x + word.width // 2, word.y + word.height // 2

    raise ValueError(f"Text not found on screen: {needle}")
