---
name: rpi-client
description: CLI client for rpi-job server. Use rpi-client to submit jobs, poll status, retrieve results, and manage remote automation tasks. Always use --json for structured output.
---

# rpi-client — Job Client (Direct)

Run from: `cd linux-agents/rpi-client && rpi-client <command>`

rpi-client is a CLI tool for interacting with rpi-job servers. It provides a convenient interface over the HTTP API.

## Commands

### start — Submit a new job

```bash
rpi-client start http://localhost:7600 "ls -la" --json
```

Response:
```json
{
  "job_id": "a3f7b2c1",
  "status": "running",
  "server_url": "http://localhost:7600"
}
```

The prompt is sent as-is to the server, which executes it as a shell command.

### status — Get job status

```bash
rpi-client status http://localhost:7600 a3f7b2c1 --json
```

Response:
```json
{
  "id": "a3f7b2c1",
  "status": "done",
  "prompt": "ls -la",
  "created_at": "2026-03-16T14:00:00Z",
  "summary": "total 16\ndrwxr-xr-x 4 user user 4096 Mar 16 14:00 .\n...",
  "updates": [
    "Starting job: ls -la",
    "Job completed successfully"
  ],
  "server_url": "http://localhost:7600"
}
```

### list — List all jobs

```bash
rpi-client list http://localhost:7600 --json
```

Response:
```json
{
  "jobs": [
    {
      "id": "a3f7b2c1",
      "status": "done",
      "prompt": "ls -la",
      "created_at": "2026-03-16T14:00:00Z"
    },
    {
      "id": "b4g8h9j0",
      "status": "running",
      "prompt": "npm test",
      "created_at": "2026-03-16T14:05:00Z"
    }
  ],
  "total": 2,
  "server_url": "http://localhost:7600"
}
```

### stop — Stop a running job

```bash
rpi-client stop http://localhost:7600 a3f7b2c1 --json
```

Response:
```json
{
  "job_id": "a3f7b2c1",
  "status": "stopped",
  "server_url": "http://localhost:7600"
}
```

Sends SIGTERM to the worker process, waits up to 5 seconds, then sends SIGKILL if still running.

### clear — Archive completed jobs

```bash
rpi-client clear http://localhost:7600 --json
```

Response:
```json
{
  "archived": 5,
  "server_url": "http://localhost:7600"
}
```

Moves all YAML files from `jobs/` to `jobs/archived/` on the server.

### logs — Stream job logs (experimental)

```bash
rpi-client logs http://localhost:7600 a3f7b2c1 --follow --json
```

Streams job updates in real-time as they're written to the YAML file.

Press Ctrl+C to stop streaming.

## Key Patterns

### Submit and poll

```bash
# Submit job
JOB_ID=$(rpi-client start http://localhost:7600 "npm test" --json | jq -r '.job_id')

# Poll until done
while true; do
  STATUS=$(rpi-client status http://localhost:7600 $JOB_ID --json | jq -r '.status')
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 1
done

# Get results
rpi-client status http://localhost:7600 $JOB_ID --json | jq -r '.summary'
```

### Integration with rpi-term and rpi-gui

```bash
# Submit terminal automation job
rpi-client start http://localhost:7600 "rpi-term run test 'npm test'"

# Submit GUI automation job
rpi-client start http://localhost:7600 "rpi-gui click --id B1"

# Submit complex job (both terminal and GUI)
rpi-client start http://localhost:7600 "bash -c 'rpi-gui type \"https://example.com\" && rpi-gui hotkey return'"
```

### Batch operations

```bash
# Submit multiple jobs
for i in {1..5}; do
  rpi-client start http://localhost:7600 "rpi-term run worker-$i 'python worker.py'"
done

# List all jobs
rpi-client list http://localhost:7600 --json | jq -r '.jobs[].id'

# Stop all running jobs
rpi-client list http://localhost:7600 --json | \
  jq -r '.jobs[] | select(.status == "running") | .id' | \
  xargs -I {} rpi-client stop http://localhost:7600 {}
```

## Output Formats

### JSON (structured)

```bash
rpi-client status http://localhost:7600 a3f7b2c1 --json
```

Returns structured JSON for parsing by other tools.

### Human-readable (default)

```bash
rpi-client status http://localhost:7600 a3f7b2c1
```

Returns formatted text for human consumption.

## Error Handling

```bash
# Server unavailable
rpi-client start http://localhost:7600 "ls -la" 2>&1
# Error: Connection refused

# Invalid job ID
rpi-client status http://localhost:7600 nonexistent --json 2>&1
# Error: Job not found

# Job failed
rpi-client status http://localhost:7600 failed_job --json | jq -r '.status'
# failed
```

Check exit codes:
- `0` — Success
- `1` — Error (connection, not found, etc.)

## Configuration

### Environment variables

```bash
# Default server URL
export RPI_JOB_URL="http://localhost:7600"

# Use default URL
rpi-client start "ls -la" --json

# Override default
rpi-client start http://remote-server:7600 "ls -la" --json
```

### Config file (optional)

Create `~/.config/rpi-client/config.yaml`:

```yaml
default_server: "http://localhost:7600"
servers:
  local: "http://localhost:7600"
  remote: "http://192.168.1.100:7600"
  staging: "http://staging.example.com:7600"
```

Then use server names:

```bash
rpi-client start local "ls -la" --json
rpi-client start remote "deploy.sh" --json
```

## Advanced Usage

### Webhook integration

```bash
# Submit job on webhook trigger
curl -X POST http://webhook-site.com/webhook \
  -d '{"trigger": "deploy"}' && \
  rpi-client start http://localhost:7600 "deploy.sh"
```

### CI/CD integration

```bash
# In GitHub Actions, GitLab CI, etc.
- name: Run automation tests
  run: |
    JOB_ID=$(rpi-client start http://192.168.1.100:7600 "npm test" --json | jq -r '.job_id')
    # Poll for completion
    rpi-client status http://192.168.1.100:7600 $JOB_ID --poll --timeout 300
    # Check results
    STATUS=$(rpi-client status http://192.168.1.100:7600 $JOB_ID --json | jq -r '.status')
    if [ "$STATUS" != "done" ]; then
      echo "Job failed"
      exit 1
    fi
```

### Monitoring

```bash
# Watch job status
watch -n 1 'rpi-client status http://localhost:7600 a3f7b2c1'

# Monitor all jobs
watch -n 5 'rpi-client list http://localhost:7600 --json | jq -r ".jobs | length"'
```

## Key Differences from macOS Direct

- **httpx instead of requests** — Async HTTP client
- **YAML job files** — Server stores jobs as YAML instead of JSON
- **Click CLI** — Uses Click framework instead of argparse
- **Same API interface** — Compatible with macOS server endpoint structure

## Rules

- **Always use `--json`** for scripting — Structured output is reliable
- **Check job status** before using results — Jobs may still be running
- **Handle errors** — Check exit codes and status fields
- **Use environment variables** for default server URL — Avoid repeating URLs
- **Use `--poll` for long-running jobs** — Don't implement polling manually
- **Keep jobs/ directory clean** — Use `clear` to archive old jobs
