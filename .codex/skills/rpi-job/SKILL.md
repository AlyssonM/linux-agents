---
name: rpi-job
description: Job server for AI agents. Use rpi-job to submit async jobs, poll status, retrieve results, and manage background work. Jobs execute commands via rpi-term or rpi-gui. Runs as FastAPI server on port 7600.
---

# rpi-job — Job Server (Listen)

Run from: `cd linux-agents/rpi-job && rpi-job`

rpi-job is a FastAPI server that accepts job submissions, executes them asynchronously, and stores results as YAML files. Think of it as a task queue for automation jobs.

## Starting the Server

```bash
# Development (auto-reload)
cd linux-agents/rpi-job && uv run uvicorn rpi_job.main:app --reload --port 7600

# Production
cd linux-agents/rpi-job && uv run uvicorn rpi_job.main:app --host 0.0.0.0 --port 7600
```

Server runs on `http://localhost:7600` by default.

## API Endpoints

### POST /job — Submit a new job

```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ls -la"}'
```

Response:
```json
{
  "job_id": "a3f7b2c1",
  "status": "running"
}
```

The job executes immediately in a subprocess worker. The worker:
1. Creates a YAML file in `jobs/<job_id>.yaml`
2. Executes the prompt as a shell command (via subprocess)
3. Updates the YAML with results
4. Marks status as "done" or "failed"

**Important:** Workers do NOT use LLM by default. They execute the prompt as a direct shell command. To use LLM interpretation, implement an optional `--llm` flag.

### GET /job/{job_id} — Get job status

```bash
curl http://localhost:7600/job/a3f7b2c1
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
    "Job completed successfully"
  ]
}
```

Possible statuses:
- `running` — Job is currently executing
- `done` — Job completed successfully
- `failed` — Job failed (error in summary)
- `stopped` — Job was manually stopped

### GET /jobs — List all jobs

```bash
curl http://localhost:7600/jobs
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
    }
  ],
  "total": 1
}
```

### POST /job/{job_id}/stop — Stop a running job

```bash
curl -X POST http://localhost:7600/job/a3f7b2c1/stop
```

Sends SIGTERM to the worker process, then SIGKILL after 5 seconds if still running.

### POST /jobs/clear — Archive completed jobs

```bash
curl -X POST http://localhost:7600/jobs/clear
```

Moves all YAML files from `jobs/` to `jobs/archived/`.

## Job File Format

Jobs are stored as YAML files:

```yaml
id: a3f7b2c1
status: done
prompt: ls -la
created_at: '2026-03-16T14:00:00Z'
summary: |
  total 16
  drwxr-xr-x 4 user user 4096 Mar 16 14:00 .
  drwxr-xr-x 3 user user 4096 Mar 16 10:00 ..
  -rw-r--r-- 1 user user  123 Mar 16 14:00 file.txt
updates:
  - 'Starting job: ls -la'
  - 'Job completed successfully'
```

## Using with rpi-client

The recommended way to interact with rpi-job is via the rpi-client CLI:

```bash
# Submit job
rpi-client start http://localhost:7600 "ls -la"

# Check status
rpi-client status http://localhost:7600 a3f7b2c1

# List jobs
rpi-client list http://localhost:7600

# Stop job
rpi-client stop http://localhost:7600 a3f7b2c1

# Clear jobs
rpi-client clear http://localhost:7600
```

## Integration with rpi-term and rpi-gui

Jobs can orchestrate both terminal and GUI automation:

```bash
# Submit a job that runs terminal commands
rpi-client start http://localhost:7600 "rpi-term run test 'npm test'"

# Submit a job that performs GUI automation
rpi-client start http://localhost:7600 "rpi-gui click --id B1"
```

The worker executes these as shell commands, so rpi-term and rpi-gui must be in PATH.

## Worker Execution Model

**Current (Default):** No LLM
```python
# Worker executes prompt as direct shell command
subprocess.run(prompt, shell=True, capture_output=True)
```

**Optional (with LLM):** Interpret prompt first
```python
# Worker uses LLM to interpret natural language
command = llm_interpret(prompt)  # "deploy latest" → "kubectl apply -f deploy.yaml"
subprocess.run(command, shell=True, capture_output=True)
```

To enable LLM interpretation, implement `llm_interpret()` in worker.py and add a flag to the job submission API.

## Key Patterns

- **Use rpi-client** — Don't use curl directly unless necessary
- **Check status before reading results** — Jobs may still be running
- **Archive old jobs** — Use `/jobs/clear` to keep the jobs/ directory clean
- **Handle failures** — Check `status` field before using `summary`
- **Use for long-running tasks** — Jobs that take more than a few seconds
- **Combine with rpi-term/rpi-gui** — Submit jobs that orchestrate complex automation

## Monitoring

Watch the jobs directory:

```bash
# Watch for new jobs
watch -n 1 'ls -la apps/rpi-job/jobs/'

# Tail job logs
tail -f apps/rpi-job/jobs/<job_id>.yaml
```

## Error Handling

Jobs fail when:
- Command returns non-zero exit code
- Command times out (default: 300 seconds)
- Worker crashes (unhandled exception)

Check the `summary` field for error details.

## Security Considerations

- **No authentication** — Server is open by default. Add API keys if exposed publicly.
- **Command injection** — Jobs run shell commands. Sanitize prompts if accepting user input.
- **Resource limits** — No limit on concurrent jobs. Consider adding rate limiting.

## Key Differences from macOS Listen

- **FastAPI instead of macOS-specific server** — Same API, different implementation
- **YAML files instead of JSON** — Easier to read and debug
- **Worker subprocess model** — Same concept, different implementation
- **No built-in LLM** — Workers execute shell commands directly (LLM is optional)

## Rules

- **Always use rpi-client** — Don't call API directly unless debugging
- **Check job status** — Don't assume jobs complete immediately
- **Archive old jobs** — Keep jobs/ directory clean
- **Handle failures** — Check status before using results
- **Use for async tasks** — Don't submit jobs that complete in < 1 second
