from __future__ import annotations

import json

import click

from rpi_gui.modules.input import click_at
from rpi_gui.modules.ocr import find_text_center
from rpi_gui.modules.screenshot import capture_screenshot


@click.command("click")
@click.option("--x", type=int, help="X coordinate")
@click.option("--y", type=int, help="Y coordinate")
@click.option("--text", "text_target", type=str, help="Click center of first OCR match")
@click.option("--button", type=click.Choice(["left", "middle", "right"]), default="left", show_default=True)
def click_cmd(x: int | None, y: int | None, text_target: str | None, button: str) -> None:
    """Click on coordinates or by locating text via OCR."""
    try:
        if text_target:
            image = capture_screenshot()
            x, y = find_text_center(image=image, needle=text_target)
        elif x is None or y is None:
            raise click.ClickException("Provide --x and --y, or use --text.")

        assert x is not None and y is not None
        click_at(x=x, y=y, button=button)
        click.echo(json.dumps({"clicked": True, "x": x, "y": y, "button": button}, ensure_ascii=False))
    except Exception as exc:
        if isinstance(exc, click.ClickException):
            raise
        raise click.ClickException(str(exc)) from exc
