# rpi-job

FastAPI job server.

## API

- `POST /job`
- `GET /job/{id}`
- `GET /jobs`
- `DELETE /job/{id}`

## Run

```bash
uv sync
uv run uvicorn rpi_job.main:app --host 0.0.0.0 --port 7600
```
