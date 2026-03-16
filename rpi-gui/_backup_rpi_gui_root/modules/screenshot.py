from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image


class ScreenshotError(RuntimeError):
    pass


def capture_screenshot() -> Image.Image:
    try:
        from PIL import ImageGrab

        return ImageGrab.grab()  # type: ignore[attr-defined]
    except Exception:
        try:
            import pyautogui

            return pyautogui.screenshot()
        except Exception as exc:
            raise ScreenshotError("Unable to capture screenshot. Ensure GUI session is active.") from exc


def save_screenshot(image: Image.Image, output_path: str | None = None) -> Path:
    output = Path(output_path) if output_path else Path("artifacts") / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output
