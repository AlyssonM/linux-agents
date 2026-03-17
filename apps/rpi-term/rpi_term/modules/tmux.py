from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass

from rpi_term.modules.errors import SessionExistsError, SessionNotFoundError, TmuxCommandError, TmuxNotFoundError

logger = logging.getLogger(__name__)


def require_tmux() -> str:
    path = shutil.which("tmux")
    if not path:
        raise TmuxNotFoundError()
    return path


def _run(args: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [require_tmux(), *args]
    logger.debug("Running tmux command: %s", " ".join(cmd))
    try:
        out = subprocess.run(cmd, capture_output=capture, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        raise TmuxCommandError(args, "tmux command timed out after 10s")
    except FileNotFoundError:
        raise TmuxNotFoundError()
    if check and out.returncode != 0:
        logger.error("tmux command failed (%s): %s", out.returncode, out.stderr.strip())
        raise TmuxCommandError(args, out.stderr.strip())
    return out


def session_exists(name: str) -> bool:
    return _run(["has-session", "-t", name], check=False).returncode == 0


def require_session(name: str) -> None:
    if not session_exists(name):
        raise SessionNotFoundError(name)


@dataclass
class SessionInfo:
    name: str
    windows: int
    created: str
    attached: bool

    def to_dict(self) -> dict:
        return vars(self)


def create_session(name: str, *, window_name: str | None = None, start_directory: str | None = None, detach: bool = True) -> None:
    if session_exists(name):
        raise SessionExistsError(name)
    args = ["new-session", "-d", "-s", name]
    if window_name:
        args += ["-n", window_name]
    if start_directory:
        args += ["-c", start_directory]
    _run(args)
    _wait_for_session(name)


def _wait_for_session(name: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if session_exists(name):
            return
        time.sleep(0.1)
    raise TmuxCommandError(["new-session", "-s", name], f"Session '{name}' did not appear within {timeout}s")


def list_sessions() -> list[SessionInfo]:
    out = _run(["list-sessions", "-F", "#{session_name}\t#{session_windows}\t#{session_created_string}\t#{session_attached}"], check=False)
    if out.returncode != 0:
        return []
    sessions = []
    for line in out.stdout.strip().splitlines():
        p = line.split("\t")
        if len(p) >= 4:
            sessions.append(SessionInfo(name=p[0], windows=int(p[1]), created=p[2], attached=p[3] != "0"))
    return sessions


def kill_session(name: str) -> None:
    require_session(name)
    _run(["kill-session", "-t", name])


def resolve_target(session: str, pane: str | None = None) -> str:
    return f"{session}:.{pane}" if pane is not None else f"{session}:"


def send_keys(session: str, keys: str, *, pane: str | None = None, enter: bool = True, literal: bool = False) -> None:
    require_session(session)
    target = resolve_target(session, pane)
    args = ["send-keys", "-t", target]
    if literal:
        args.append("-l")
    args.append(keys)
    _run(args)
    if enter:
        _run(["send-keys", "-t", target, "Enter"])


def capture_pane(session: str, *, pane: str | None = None, start_line: int | None = None, end_line: int | None = None) -> str:
    require_session(session)
    target = resolve_target(session, pane)
    args = ["capture-pane", "-p", "-t", target]
    if start_line is not None:
        args += ["-S", str(start_line)]
    if end_line is not None:
        args += ["-E", str(end_line)]
    return _run(args).stdout.rstrip("\n")
