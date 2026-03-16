from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, list_running_apps, to_json


@click.group(name="apps", help="Application discovery commands")
def apps_cmd() -> None:
    pass


@apps_cmd.command(name="list", help="List running applications")
def apps_list_cmd() -> None:
    try:
        click.echo(to_json({"apps": list_running_apps()}))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
