import click


class RpiTermError(click.ClickException):
    code: str = "error"

    def to_dict(self) -> dict:
        return {"ok": False, "error": self.code, "message": self.message}


class TmuxNotFoundError(RpiTermError):
    code = "tmux_not_found"

    def __init__(self):
        super().__init__("tmux not found in PATH. Install with: sudo apt install tmux")


class SessionNotFoundError(RpiTermError):
    code = "session_not_found"

    def __init__(self, name: str):
        super().__init__(f"Session not found: {name}")
        self.session = name


class SessionExistsError(RpiTermError):
    code = "session_exists"

    def __init__(self, name: str):
        super().__init__(f"Session already exists: {name}")


class CommandTimeoutError(RpiTermError):
    code = "timeout"

    def __init__(self, session: str, cmd: str, timeout: float):
        super().__init__(f"Command timed out after {timeout}s in session '{session}': {cmd[:80]}")


class TmuxCommandError(RpiTermError):
    code = "tmux_error"

    def __init__(self, cmd: list[str], stderr: str):
        super().__init__(f"tmux {' '.join(cmd)}: {stderr}")


class PatternNotFoundError(RpiTermError):
    code = "pattern_not_found"

    def __init__(self, pattern: str, session: str, timeout: float):
        super().__init__(f"Pattern '{pattern}' not found in session '{session}' within {timeout}s")
