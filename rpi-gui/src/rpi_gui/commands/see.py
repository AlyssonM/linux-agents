from __future__ import annotations

import json

import click

from rpi_gui.modules.ocr import run_ocr
from rpi_gui.modules.screenshot import capture_screenshot_to_file, capture_screenshot, save_screenshot


@click.command("see")
@click.option("--output", type=click.Path(dir_okay=False, path_type=str), help="Output PNG path")
@click.option("--ocr", "with_ocr", is_flag=True, help="Run OCR and include extracted words")
@click.option("--force-pil", is_flag=True, help="Force Python capture (PIL/pyautogui) instead of grim/scrot")
def see_cmd(output: str | None, with_ocr: bool, force_pil: bool) -> None:
    """
    Capture current screen and optionally OCR text elements.
    
    Uses grim (Wayland) or scrot (X11) by default for best compatibility.
    Use --force-pil to use Python libraries (may not work in Wayland).
    """
    try:
        if force_pil:
            # Legacy behavior: use Python libraries
            image = capture_screenshot()
            saved = save_screenshot(image=image, output_path=output)
        else:
            # New behavior: use external tools (grim/scrot) for Wayland support
            saved = capture_screenshot_to_file(output_path=output)
            # Load image for OCR or metadata
            from PIL import Image
            image = Image.open(saved)

        payload: dict[str, object] = {
            "screenshot": str(saved),
            "width": image.width,
            "height": image.height,
        }

        if with_ocr:
            ocr_result = run_ocr(image)
            payload["text"] = ocr_result.text
            payload["elements"] = [
                {
                    "text": w.text,
                    "x": w.x,
                    "y": w.y,
                    "width": w.width,
                    "height": w.height,
                    "confidence": w.confidence,
                }
                for w in ocr_result.words
            ]

        click.echo(json.dumps(payload, ensure_ascii=False))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
