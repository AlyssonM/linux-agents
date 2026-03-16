from __future__ import annotations

import click

from rpi_gui.modules.input import focus_window


@click.command("focus", help="Focus window by title using xdotool")
@click.argument("window_query")
@click.option("--exact", is_flag=True, help="Match exact window title")
def focus_cmd(window_query: str, exact: bool) -> None:
    try:
        window_id = focus_window(window_query, exact=exact)
        click.echo(f"focused window {window_id}")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
