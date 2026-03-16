# listen

Codex-focused HTTP job server for `linux-agents`.

This is the Linux/Raspberry Pi adaptation of `mac-mini-agent/apps/listen/`, but:

- uses **Codex CLI** instead of Claude
- uses prompts from **`.codex/`**
- uses **tmux on Linux** instead of Terminal.app automation
- has **no justfile dependency**

## What it does

- accepts jobs over HTTP
- stores job state in YAML
- spawns a worker per job
- runs `codex exec` inside a tmux session
- lets the Codex agent use `rpi-gui` and `rpi-term`
- tracks status, updates, summary, exit code, and duration

## Run

```bash
cd listen
uv run python main.py
```

Server starts on port `7600` by default.

## Endpoints

- `POST /job` — submit a new job
- `GET /job/{id}` — fetch full YAML job
- `GET /jobs` — list jobs summary
- `POST /jobs/clear` — archive jobs
- `DELETE /job/{id}` — stop a running job

## Requirements

- `codex` installed and authenticated
- `tmux` installed
- repo checked out locally
- `.codex/agents/job-system-prompt.md` present
- `.codex/commands/rpi-gui-term-user-prompt.md` present

## Notes

This app is intentionally separate from `rpi-job/`.

- `rpi-job/` = simple generic subprocess shell job server
- `listen/` = agent-oriented Codex job server, closer to the original Mac Mini Agent concept
