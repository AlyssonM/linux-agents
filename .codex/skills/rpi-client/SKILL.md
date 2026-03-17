---
name: rpi-client
description: CLI client for rpi-job server. Use rpi-client to submit jobs, poll status, retrieve results, and manage remote automation tasks. Always use --json for structured output.
---

# rpi-client — Job Client (Direct)

Run from: `cd linux-agents/apps/rpi-client && rpi-client <command>`

rpi-client is a CLI tool for interacting with rpi-job servers.

## Commands

### start — Submit a new job

```bash
rpi-client start http://localhost:7600 "ls -la"
```

The prompt is sent to the server, which executes it as a shell command.

### get — Get job status and results

```bash
rpi-client get http://localhost:7600 <job_id>
```

### latest — Get most recent job

```bash
rpi-client latest http://localhost:7600
```

### list — List all jobs

```bash
rpi-client list http://localhost:7600
rpi-client list http://localhost:7600 --archived
```

### stop — Stop a running job

```bash
rpi-client stop http://localhost:7600 <job_id>
```

## Key Patterns

- **Check job status** before using results — Jobs may still be running.
- **Use URL** as the first argument for all commands.
- **Job ID** is required for `get` and `stop`.

## Rules

- **Check exit codes** — `0` for success, `1` for error.
- **Job lifecycle**: `start` -> `get` (poll) -> `stop` (if needed).
