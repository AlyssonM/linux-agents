import json
import sys
import click
from rpi_term.modules.errors import RpiTermError


def emit(data: dict, *, as_json: bool, human_lines: list[str] | str) -> None:
    if as_json:
        click.echo(json.dumps(data, separators=(",", ":")))
        return
    if isinstance(human_lines, str):
        click.echo(human_lines)
    else:
        for line in human_lines:
            click.echo(line)


def emit_error(err: RpiTermError, *, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(err.to_dict(), separators=(",", ":")))
    else:
        click.echo(f"Error: {err.message}", err=True)
    sys.exit(1)
