import click
import subprocess
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


@session.command("attach")
@click.option("--name", required=True, help="Session name to attach")
@click.option("--geometry", default="900x600", help="Window geometry (default: 900x600)")
@click.option("--display", default=":0", help="X11 display (default: :0)")
@click.option("--json", "as_json", is_flag=True)
def attach(name: str, geometry: str, display: str, as_json: bool):
    """Attach to tmux session in lxterminal on VNC."""
    try:
        # Verificar se sessão existe
        if not tmux.session_exists(name):
            raise RpiTermError(f"Session '{name}' does not exist")

        # Abrir lxterminal anexado à sessão
        cmd = [
            "lxterminal",
            f"--geometry={geometry}",
            "-e",
            f"tmux attach-session -t {name}"
        ]

        env = {"DISPLAY": display}

        subprocess.Popen(
            cmd,
            env=env,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        emit(
            {"ok": True, "action": "attach", "session": name, "display": display, "geometry": geometry},
            as_json=as_json,
            human_lines=f"Attached to session: {name} on {display} (geometry: {geometry})"
        )
    except RpiTermError as e:
        emit_error(e, as_json=as_json)
