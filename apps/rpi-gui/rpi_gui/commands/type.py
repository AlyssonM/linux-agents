from __future__ import annotations

import json

import click

from rpi_gui.modules.input import type_text


@click.command("type")
@click.argument("text", type=str)
@click.option("--interval", type=float, default=0.0, show_default=True, help="Delay between keystrokes")
@click.option("--enter", "press_enter", is_flag=True, help="Press Enter after typing")
def type_cmd(text: str, interval: float, press_enter: bool) -> None:
    """Type text into currently focused input."""
    try:
        type_text(text=text, interval=interval, press_enter=press_enter)
        click.echo(json.dumps({"typed": True, "chars": len(text), "enter": press_enter}, ensure_ascii=False))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
