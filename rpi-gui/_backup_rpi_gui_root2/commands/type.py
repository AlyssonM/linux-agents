from __future__ import annotations

import json

import click

from rpi_gui.modules.input import InputError
from rpi_gui.modules.input import type_text as raw_type_text


def type_text(text: str, interval: float = 0.0, press_enter: bool = False) -> None:
    try:
        raw_type_text(text=text, interval=interval, press_enter=press_enter)
    except (InputError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.command(name="type", help="Type text into active window")
@click.argument("text", type=str)
@click.option("--interval", type=float, default=0.0, show_default=True)
@click.option("--enter", "press_enter", is_flag=True, default=False)
def type_cmd(text: str, interval: float, press_enter: bool) -> None:
    try:
        type_text(text=text, interval=interval, press_enter=press_enter)
        click.echo(json.dumps({"typed": True, "chars": len(text), "enter": press_enter}, ensure_ascii=False))
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
