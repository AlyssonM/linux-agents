# listen

High-level REST job server used by the Linux Agents stack on port `7600`.

## What It Does

- accepts jobs over HTTP
- stores job state in YAML files under `apps/listen/jobs/`
- spawns workers to execute prompts via configured agent runtimes
- exposes endpoints to create, inspect, list, archive, and stop jobs

## API

- `POST /job`
- `GET /job/{id}`
- `GET /jobs`
- `POST /jobs/clear`
- `DELETE /job/{id}`

## Run

```bash
cd apps/listen
uv run python main.py
```

## Example Requests

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt":"escreva um script para monitorar CPU","agent":"opencode"}'

curl http://127.0.0.1:7600/job/<job_id>
curl http://127.0.0.1:7600/jobs
```

## Companion CLI

```bash
uv run rpi-client start http://127.0.0.1:7600 "minha tarefa" --agent opencode
```

## Related Components

- `rpi-client` is the primary CLI client for this server
- `rpi-job` is a simpler job-server implementation
- `openclaw-listen` is the OpenClaw-focused listener variant
