from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, find_elements, to_json


@click.command(name="find", help="Find UI elements via accessibility tree")
@click.option("--text", required=False, help="Text/name to search")
@click.option("--role", "role_name", required=False, help="Role filter (e.g. button, text)")
@click.option("--app", "app_name", required=False, help="Application name filter")
@click.option("--exact", is_flag=True, help="Use exact text match")
@click.option("--max-results", default=50, show_default=True, type=int)
def find_cmd(
    text: str | None,
    role_name: str | None,
    app_name: str | None,
    exact: bool,
    max_results: int,
) -> None:
    if text is None and role_name is None and app_name is None:
        raise click.ClickException("Provide at least one filter: --text, --role, or --app")

    try:
        elements = find_elements(
            text=text,
            role=role_name,
            app=app_name,
            exact=exact,
            max_results=max_results,
        )
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(to_json({"count": len(elements), "elements": elements}))
