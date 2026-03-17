import click
from rpi_term.modules import sentinel
from rpi_term.modules.errors import RpiTermError
from rpi_term.modules.output import emit, emit_error


@click.command()
@click.option("--session", "session_name", required=True)
@click.argument("cmd")
@click.option("--timeout", default=30.0)
@click.option("--pane", default=None)
@click.option("--json", "as_json", is_flag=True)
def run(session_name: str, cmd: str, timeout: float, pane: str | None, as_json: bool):
    try:
        exit_code, output = sentinel.run_and_wait(session_name, cmd, pane=pane, timeout=timeout)
        emit({"ok": exit_code == 0, "session": session_name, "command": cmd, "exit_code": exit_code, "output": output}, as_json=as_json, human_lines=output)
        if exit_code != 0:
            raise SystemExit(exit_code)
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
