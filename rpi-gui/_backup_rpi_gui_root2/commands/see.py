from __future__ import annotations

import json

import click

from rpi_gui.modules.ocr import run_ocr
from rpi_gui.modules.screenshot import capture_screenshot, save_screenshot


@click.command(name="see", help="Capture screenshot and optional OCR elements")
@click.option("--output", type=click.Path(dir_okay=False, path_type=str), default=None)
@click.option("--ocr", "with_ocr", is_flag=True, default=False)
def see_cmd(output: str | None, with_ocr: bool) -> None:
    try:
        image = capture_screenshot()
        saved = save_screenshot(image=image, output_path=output)
        payload: dict[str, object] = {
            "screenshot": str(saved),
            "width": image.width,
            "height": image.height,
        }
        if with_ocr:
            result = run_ocr(image)
            payload["text"] = result.text
            payload["elements"] = [w.__dict__ for w in result.words]
        click.echo(json.dumps(payload, ensure_ascii=False))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
