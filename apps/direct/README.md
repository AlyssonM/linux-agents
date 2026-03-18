# direct

CLI client for the Codex-focused `listen/` server in `linux-agents`.

## Role

- `listen/` = agent-native Codex job server
- `direct/` = CLI for submitting and inspecting those jobs

## Setup

```bash
uv sync
uv run direct --help
```

## Examples

```bash
uv run direct start http://127.0.0.1:7600 "Open Chromium and inspect the page"

uv run direct get http://127.0.0.1:7600 <job_id>

uv run direct latest http://127.0.0.1:7600 1

uv run direct stop http://127.0.0.1:7600 <job_id>
```

## Difference vs rpi-client

- `rpi-client/` pairs with `rpi-job/` (generic shell-job flow)
- `direct/` pairs with `listen/` (Codex-agent flow)
