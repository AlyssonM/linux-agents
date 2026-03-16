from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, list_running_apps, to_json


@click.group(help="Application discovery commands")
def apps() -> None:
    pass


@apps.command(name="list", help="List running applications")
def apps_list() -> None:
    try:
        data = {"apps": list_running_apps()}
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(to_json(data))
