from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image


def capture_screenshot() -> Image.Image:
    """Capture screenshot using Pillow ImageGrab, fallback to pyautogui."""
    try:
        from PIL import ImageGrab

        return ImageGrab.grab()  # type: ignore[attr-defined]
    except Exception:
        try:
            import pyautogui

            return pyautogui.screenshot()
        except Exception as exc:
            raise RuntimeError(
                "Unable to capture screenshot. Ensure a GUI session is active."
            ) from exc


def save_screenshot(image: Image.Image, output_path: str | None = None) -> Path:
    output = (
        Path(output_path)
        if output_path
        else Path("artifacts") / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output
