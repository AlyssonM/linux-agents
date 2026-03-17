# openclaw-listen

OpenClaw-native async job listener for `linux-agents`.

This component is complementary to the existing job-server flows:

- `rpi-job/` = simple generic subprocess shell jobs
- `listen/` = external agent CLI runtime (`codex exec` + tmux)
- `openclaw-listen/` = OpenClaw-native runtime via subagent

## What it does

- accepts jobs over HTTP
- stores job state in YAML
- spawns an async worker per job
- runs work through the local OpenClaw agent (`openclaw agent --message`)
- optionally delivers friendly responses back to a chat channel/target via OpenClaw delivery

## Current behavior

- `execution.strategy=auto` resolves to `subagent`
- all strategies (`auto`, `subagent`) use the subagent execution path
- each job runs in an isolated Python subprocess that calls `openclaw agent`
- cancellation is best-effort and currently targets the worker process
- delivery uses OpenClaw's `--reply-channel` and `--reply-to` flags; `delivery.reply_to` is stored as metadata only for now

## Run

```bash
cd openclaw-listen
python main.py
```

or:

```bash
uvicorn main:app --host 0.0.0.0 --port 7610
```

## API

- `POST /jobs` — create a job
- `GET /jobs/{id}` — get full YAML job
- `GET /jobs` — list jobs summary
- `POST /jobs/clear` — archive all jobs
- `POST /jobs/{id}/cancel` — best-effort cancellation

`POST /jobs` returns HTTP `202` with both `id` and `job_id`, plus `status_url`, to stay convenient for machines and humans.

`GET /jobs` supports a small set of filters:

- `archived=true`
- `status=<queued|planning|running|succeeded|failed|cancelled>`
- `source_type=<rest|direct|telegram|discord|gateway>`

## Example payload

```json
{
  "instruction": "Abra o Chromium e me diga o que está aberto na tela",
  "execution": {
    "strategy": "auto",
    "timeout_seconds": 120,
    "thinking": "low"
  },
  "source": {
    "type": "telegram",
    "chat_id": "1129943309",
    "message_id": "123"
  },
  "delivery": {
    "mode": "reply",
    "channel": "telegram",
    "reply_to": "123"
  }
}
```

## Design goals

- Isolated jobs via Python subprocesses (one worker per job)
- Poll-based by default, with optional push delivery for chat integration
- FastAPI async workers (one worker process per job)
- YAML job state on disk (simple, debuggable)
- Direct OpenClaw CLI invocation via `openclaw agent`

## Architecture

```
openclaw-listen/
├── main.py          # FastAPI app (REST API)
├── worker.py        # Job worker (spawns subagent subprocess)
├── jobs/            # Job state YAML files
└── archived/        # Completed jobs
```

### Job lifecycle

1. HTTP POST to `/jobs` creates job YAML
2. `main.py` spawns `worker.py <job_id>` subprocess
3. Worker reads job YAML
4. Worker creates temporary Python script
5. Python script calls `openclaw agent --message <instruction>`
6. OpenClaw agent executes instruction
7. Result captured and written to job YAML
8. HTTP GET polls job status until completion
9. Optional: delivery back to chat channel

## Concurrency

By default, multiple jobs run in parallel (one worker process per job).

The FastAPI server itself is async, but job execution is synchronous per worker.

No limit on concurrent jobs is enforced by `openclaw-listen` itself; it's up to you to set limits:

- Add a semaphore in `main.py` before spawning workers
- Add a queue system (e.g., Redis) if you need distributed job processing
- Use system resource limits (ulimit, cgroups) if running many workers in parallel

## Testing

```bash
# Create a test job
curl -X POST http://localhost:7610/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "List the files in the current directory",
    "execution": {"strategy": "auto", "timeout_seconds": 30}
  }'

# Check job status
curl http://localhost:7610/jobs/<id>
```

## Deployment

### Systemd service

```ini
[Unit]
Description=openclaw-listen job server
After=network.target

[Service]
Type=simple
User=alyssonpi
WorkingDirectory=/home/alyssonpi/.openclaw/workspace/linux-agents/openclaw-listen
Environment="PATH=/home/alyssonpi/.openclaw/workspace/linux-agents/.venv/bin"
ExecStart=/home/alyssonpi/.openclaw/workspace/linux-agents/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable with:

```bash
sudo ln -s /etc/systemd/system/openclaw-listen.service \
  ~/.config/systemd/user/openclaw-listen.service
systemctl --user daemon-reload
systemctl --user enable openclaw-listen
systemctl --user start openclaw-listen
```

## Future work

- [ ] Add worker pool / concurrency limits
- [ ] Implement real delivery integration (not just metadata)
- [ ] Add job priority queue
- [ ] Support for streaming results (Server-Sent Events)
- [ ] Metrics / monitoring (Prometheus)
- [ ] Web UI for job management
- [ ] Retry logic for transient failures
- [ ] Better error messages and debugging tools
