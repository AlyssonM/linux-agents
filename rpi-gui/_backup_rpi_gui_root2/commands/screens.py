from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, list_screens, to_json


@click.group(help="Screen/monitor commands")
def screens() -> None:
    pass


@screens.command(name="list", help="List available screens")
def screens_list() -> None:
    try:
        data = {"screens": list_screens()}
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(to_json(data))
