# rpi-term

tmux-based terminal automation CLI.

## Commands

- `rpi-term session create --name agent-1`
- `rpi-term run --session agent-1 "npm test"`
- `rpi-term send --session agent-1 "ls -la"`
- `rpi-term logs --session agent-1`
- `rpi-term poll --session agent-1 --until "DONE"`
- `rpi-term fanout --sessions a1,a2,a3 "build"`

## Dev

```bash
uv sync
uv run pytest
```
