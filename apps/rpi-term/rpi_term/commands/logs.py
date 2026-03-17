import click
from rpi_term.modules import tmux
from rpi_term.modules.errors import RpiTermError
from rpi_term.modules.output import emit, emit_error


@click.command()
@click.option("--session", "session_name", required=True)
@click.option("--pane", default=None)
@click.option("--lines", type=int, default=200)
@click.option("--json", "as_json", is_flag=True)
def logs(session_name: str, pane: str | None, lines: int, as_json: bool):
    try:
        content = tmux.capture_pane(session_name, pane=pane, start_line=-abs(lines))
        emit({"ok": True, "session": session_name, "content": content}, as_json=as_json, human_lines=content)
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
