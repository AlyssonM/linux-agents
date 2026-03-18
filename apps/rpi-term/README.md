# rpi-term

tmux-based terminal automation CLI for persistent and scriptable shell sessions.

## Commands

- `session create|attach|kill|list` manages tmux-backed sessions
- `run` executes a command and captures output
- `send` sends keys/commands to an existing session
- `logs` retrieves recent output from a session
- `poll` waits until a condition appears in session output
- `fanout` runs the same command across multiple sessions

## Quick Start

```bash
uv sync
uv run rpi-term --help
uv run rpi-term session create --name agent-1
uv run rpi-term run --session agent-1 "npm test"
```

## Testing

```bash
uv run pytest -q
```
