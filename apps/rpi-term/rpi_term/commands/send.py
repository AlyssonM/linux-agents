import click
from rpi_term.modules import tmux
from rpi_term.modules.errors import RpiTermError
from rpi_term.modules.output import emit, emit_error


@click.command()
@click.option("--session", "session_name", required=True)
@click.argument("text")
@click.option("--pane", default=None)
@click.option("--enter/--no-enter", default=True)
@click.option("--json", "as_json", is_flag=True)
def send(session_name: str, text: str, pane: str | None, enter: bool, as_json: bool):
    try:
        tmux.send_keys(session_name, text, pane=pane, enter=enter, literal=True)
        emit({"ok": True, "action": "send", "session": session_name, "text": text, "enter": enter}, as_json=as_json, human_lines=f"Sent to {session_name}: {text}")
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
