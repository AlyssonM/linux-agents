from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, list_screens, to_json


@click.group(name="screens", help="Screen commands")
def screens_cmd() -> None:
    pass


@screens_cmd.command(name="list", help="List available screens")
def screens_list_cmd() -> None:
    try:
        click.echo(to_json({"screens": list_screens()}))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
