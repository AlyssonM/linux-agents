import re
import time
import click
from rpi_term.modules import tmux
from rpi_term.modules.errors import PatternNotFoundError, RpiTermError
from rpi_term.modules.output import emit, emit_error


@click.command()
@click.option("--session", "session_name", required=True)
@click.option("--until", "pattern", required=True)
@click.option("--timeout", default=30.0)
@click.option("--interval", default=0.5)
@click.option("--pane", default=None)
@click.option("--json", "as_json", is_flag=True)
def poll(session_name: str, pattern: str, timeout: float, interval: float, pane: str | None, as_json: bool):
    if timeout < 0:
        raise click.ClickException("timeout must be >= 0")
    if interval <= 0:
        raise click.ClickException("interval must be > 0")
    try:
        rgx = re.compile(pattern)
    except re.error as e:
        click.echo(f"Error: Invalid regex: {e}", err=True)
        raise SystemExit(1)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            content = tmux.capture_pane(session_name, pane=pane, start_line=-200)
            m = rgx.search(content)
            if m:
                emit({"ok": True, "session": session_name, "match": m.group(0), "content": content}, as_json=as_json, human_lines=content)
                return
            time.sleep(interval)
        raise PatternNotFoundError(pattern, session_name, timeout)
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
