from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click

from rpi_gui.modules.ocr import run_ocr
from rpi_gui.modules.screenshot import capture_screenshot


@click.command("ocr")
@click.option("--output", type=click.Path(dir_okay=False, path_type=str), help="Write OCR JSON output to file")
@click.option("--min-confidence", type=float, default=0.0, show_default=True)
def ocr_cmd(output: str | None, min_confidence: float) -> None:
    """Run Tesseract OCR on a fresh screenshot."""
    try:
        image = capture_screenshot()
        result = run_ocr(image=image, min_confidence=min_confidence)
        payload = {
            "text": result.text,
            "elements": [
                {
                    "text": w.text,
                    "x": w.x,
                    "y": w.y,
                    "width": w.width,
                    "height": w.height,
                    "confidence": w.confidence,
                }
                for w in result.words
            ],
        }

        if output:
            out = Path(output)
        else:
            out = Path("artifacts") / f"ocr-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        click.echo(json.dumps({"output": str(out), "elements": len(result.words)}, ensure_ascii=False))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
