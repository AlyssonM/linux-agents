from __future__ import annotations

import json

import click

from rpi_gui.modules.input import InputError
from rpi_gui.modules.input import click_at as raw_click_at
from rpi_gui.modules.ocr import find_text_center
from rpi_gui.modules.screenshot import capture_screenshot


def click_at(x: int, y: int, button: str = "left") -> None:
    try:
        raw_click_at(x=x, y=y, button=button)
    except (InputError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.command(name="click", help="Click coordinates or OCR text target")
@click.option("--x", type=int, default=None)
@click.option("--y", type=int, default=None)
@click.option("--text", "text_target", type=str, default=None)
@click.option("--button", type=click.Choice(["left", "middle", "right"]), default="left")
def click_cmd(x: int | None, y: int | None, text_target: str | None, button: str) -> None:
    try:
        if text_target:
            x, y = find_text_center(capture_screenshot(), text_target)
        elif x is None or y is None:
            raise click.ClickException("Provide --x and --y, or use --text.")

        assert x is not None and y is not None
        click_at(x, y, button=button)
        click.echo(json.dumps({"clicked": True, "x": x, "y": y, "button": button}, ensure_ascii=False))
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
