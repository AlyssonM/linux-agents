# direct

CLI client for the Codex-focused `listen/` server in `linux-agents`.

This is the Linux adaptation of `mac-mini-agent/apps/direct/`, designed to pair with `listen/`.

## Role

- `listen/` = agent-native Codex job server
- `direct/` = CLI for submitting and inspecting those jobs

## Run

```bash
cd direct
uv run python main.py --help
```

## Examples

```bash
# submit a job
direct start http://127.0.0.1:7600 "Open Chromium and inspect the page"

# inspect a job
direct get http://127.0.0.1:7600 <job_id>

# latest job
direct latest http://127.0.0.1:7600 1

# stop a job
direct stop http://127.0.0.1:7600 <job_id>
```

## Difference vs rpi-client

- `rpi-client/` pairs with `rpi-job/` (generic shell-job flow)
- `direct/` pairs with `listen/` (Codex-agent flow)
