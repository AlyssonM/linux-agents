import re
import time
import uuid
from rpi_term.modules import tmux
from rpi_term.modules.errors import CommandTimeoutError


def generate_token() -> str:
    return uuid.uuid4().hex[:8]


def wrap_command(cmd: str, token: str) -> str:
    return f'echo "__START_{token}" ; {cmd} ; echo "__DONE_{token}:$?"'


def detect_completion(captured: str, token: str) -> tuple[bool, int | None, str]:
    done = re.search(rf"^__DONE_{re.escape(token)}:(\d+)\s*$", captured, re.MULTILINE)
    if not done:
        return (False, None, "")
    start = re.search(rf"^__START_{re.escape(token)}\s*$", captured, re.MULTILINE)
    output = captured[start.end():done.start()].strip() if start else captured[:done.start()].strip()
    return (True, int(done.group(1)), output)


def run_and_wait(session: str, cmd: str, *, pane: str | None = None, timeout: float = 30.0, poll_interval: float = 0.2) -> tuple[int, str]:
    token = generate_token()
    tmux.send_keys(session, wrap_command(cmd, token), pane=pane, enter=True, literal=False)
    deadline = None if timeout == 0 else time.monotonic() + timeout
    while deadline is None or time.monotonic() < deadline:
        time.sleep(poll_interval)
        captured = tmux.capture_pane(session, pane=pane, start_line=-500)
        found, code, output = detect_completion(captured, token)
        if found:
            return code or 0, output
    raise CommandTimeoutError(session, cmd, timeout)
