# rpi-job

Lightweight FastAPI job server for subprocess-based task execution.

## API

- `POST /job`
- `GET /job/{id}`
- `GET /jobs`
- `DELETE /job/{id}`

## Run Locally

```bash
uv sync
uv run uvicorn rpi_job.main:app --host 0.0.0.0 --port 7600
```

## Example

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt":"echo hello","agent":"codex"}'
```

## Notes

- `rpi-client` is the companion CLI for this API
- job state is exposed via the API and stored by the server runtime
