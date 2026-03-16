import click
from rpi_term.modules import tmux
from rpi_term.modules.errors import RpiTermError
from rpi_term.modules.output import emit, emit_error


@click.group()
def session():
    """Manage tmux sessions."""


@session.command("create")
@click.option("--name", required=True)
@click.option("--window", default=None)
@click.option("--dir", "start_dir", default=None)
@click.option("--json", "as_json", is_flag=True)
def create(name: str, window: str | None, start_dir: str | None, as_json: bool):
    try:
        tmux.create_session(name, window_name=window, start_directory=start_dir, detach=True)
        emit({"ok": True, "action": "create", "session": name}, as_json=as_json, human_lines=f"Created session: {name}")
    except RpiTermError as e:
        emit_error(e, as_json=as_json)


@session.command("list")
@click.option("--json", "as_json", is_flag=True)
def list_cmd(as_json: bool):
    try:
        sessions = tmux.list_sessions()
        if as_json:
            emit({"ok": True, "sessions": [s.to_dict() for s in sessions]}, as_json=True, human_lines="")
        else:
            for s in sessions:
                click.echo(f"{s.name}\t{s.windows}\t{s.created}\t{'attached' if s.attached else 'detached'}")
    except RpiTermError as e:
        emit_error(e, as_json=as_json)


@session.command("kill")
@click.option("--name", required=True)
@click.option("--json", "as_json", is_flag=True)
def kill(name: str, as_json: bool):
    try:
        tmux.kill_session(name)
        emit({"ok": True, "action": "kill", "session": name}, as_json=as_json, human_lines=f"Killed session: {name}")
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
