from __future__ import annotations

import click

from rpi_gui.modules.accessibility import AccessibilityError, find_elements, to_json


@click.command(name="find", help="Find accessibility elements")
@click.option("--text", default=None)
@click.option("--role", default=None)
@click.option("--app", default=None)
@click.option("--exact", is_flag=True, default=False)
@click.option("--max-results", type=int, default=50)
def find_cmd(text: str | None, role: str | None, app: str | None, exact: bool, max_results: int) -> None:
    if not any([text, role, app]):
        raise click.ClickException("Provide at least one filter: --text, --role, or --app")

    try:
        elements = find_elements(text=text, role=role, app=app, exact=exact, max_results=max_results)
        click.echo(to_json({"count": len(elements), "elements": elements}))
    except AccessibilityError as exc:
        raise click.ClickException(str(exc)) from exc
