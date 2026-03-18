# rpi-client

CLI HTTP client for `rpi-job` and compatible job servers.

## Commands

- `start` submits a new job
- `get` fetches one job by id
- `list` lists jobs
- `stop` requests job cancellation
- `latest` prints the most recent jobs

## Usage

```bash
uv run rpi-client start http://127.0.0.1:7600 "Open Firefox"
uv run rpi-client list http://127.0.0.1:7600
uv run rpi-client get http://127.0.0.1:7600 <job_id>
uv run rpi-client stop http://127.0.0.1:7600 <job_id>
```

## Setup

```bash
uv sync
uv run rpi-client --help
```
