# Job Server Workflow E2E Report

- **Spec:** `linux-agents/specs/job-server-workflow.md`
- **Artifact dir:** `artifacts/e2e/20260316-1255`
- **Server command:** `PYTHONPATH=/home/alyssonpi/.openclaw/workspace/linux-agents/rpi-job:/home/alyssonpi/.openclaw/workspace/linux-agents/rpi-client /home/alyssonpi/.openclaw/workspace/linux-agents/.venv/bin/python -m rpi_job.main`
- **Server log:** `artifacts/e2e/20260316-1255/server.log`
- **Base URL:** `http://127.0.0.1:7600`

## Summary

**Overall:** PARTIAL GREEN / PASS WITH FINDINGS

The FastAPI server started successfully, accepted HTTP requests, created async worker jobs, and `rpi-client start/get/list/stop` all worked against the live server. Concurrent job submission also worked.

Two important issues were found:
1. `latest -n` did **not** return the newest submitted jobs; it returned the last jobs in YAML filename sort order instead.
2. API validation allows a whitespace-only prompt via raw HTTP (`POST /job`), even though the client blocks empty input.

There was also a stop-race inconsistency: a stopped job still contained a completed summary/updates from the worker.

## Pass / Fail Matrix

| Step | Result | Notes |
|---|---|---|
| Server start | PASS | Server became reachable after 9 checks; startup ~1.97s |
| Reachability check | PASS | `GET /jobs` returned 200 |
| Submit primary job | PASS | Job `53c3529e` created |
| Fetch job by id | PASS | `get` returned YAML |
| Poll to terminal state | PASS | Primary job reached `done` |
| `list` command | PASS | Returned visible jobs including new job |
| `latest -n 1` | FAIL | Returned older job `cfe7d02d`, not newest `53c3529e` |
| Concurrent submissions | PASS | Jobs `47119b48` and `06dc027f` created successfully |
| Compare concurrent status progression | PASS | One job stopped, one completed |
| Stop active job | PASS with finding | `stop` returned `stopped`, but YAML still showed completed updates/summary |
| Clear/archive jobs | PASS with finding | `POST /jobs/clear` archived 13 jobs, including a still-running invalid-prompt job |
| Error handling: missing job | PASS | 404 surfaced correctly via client |
| Error handling: invalid prompt | FAIL | Server accepted whitespace-only prompt and created job `25f118bc` |

## Jobs Submitted In This Run

- Primary: `53c3529e` → `done`
- Concurrent A: `47119b48` → `stopped`
- Concurrent B: `06dc027f` → `done`
- Invalid prompt via raw HTTP: `25f118bc` → accepted unexpectedly, later archived while still `running`

## Status Progression

### `53c3529e`
- initial `running`
- final `done`
- final summary: `Completed: job server e2e test`

### `47119b48`
- created `running`
- stop request succeeded
- observed final status `stopped`
- **finding:** final YAML still had:
  - `updates: [step 1/3, step 2/3, step 3/3]`
  - `summary: 'Completed: concurrent job alpha'`

### `06dc027f`
- created `running`
- final `done`
- final summary: `Completed: concurrent job beta`

## Key Evidence

### Server startup
- Log shows normal FastAPI/Uvicorn boot and clean shutdown.
- Metric: `server_startup_seconds=1.966`

### Primary async execution
`job1-get-final.yaml`:
- status `done`
- 3 worker updates present
- summary written correctly

### Concurrency
- `47119b48` and `06dc027f` were submitted back-to-back.
- Both got unique job IDs and separate worker PIDs.
- No YAML corruption or partial-write evidence was observed.

### Stop behavior finding
`47119b48-final.yaml` contains:
- `status: stopped`
- but also full completion output

This suggests a race: the stop endpoint overwrites status, but the worker may already have written completion data before termination.

### `latest` behavior finding
Artifacts:
- `list-after-job1.yaml` includes newly-created `53c3529e`
- `latest-1.yaml` returned older job `cfe7d02d`
- `latest-3.yaml` returned older jobs based on sorted YAML order, not `created_at`

Likely cause: `latest_jobs()` uses the tail of `list_jobs()` output, and `/jobs` sorts by filename, not creation timestamp.

### Invalid prompt validation finding
Raw HTTP test:
- request: `POST /job` with `{"prompt":"   "}`
- response: `{"job_id":"25f118bc","status":"running"}`

Likely cause: Pydantic `min_length=1` accepts whitespace-only strings; server does not strip/validate prompt content.

## YAML Artifact Paths

From `server-yaml-paths.txt` after archival:
- `rpi-job/rpi_job/jobs/archived/53c3529e.yaml`
- `rpi-job/rpi_job/jobs/archived/47119b48.yaml`
- `rpi-job/rpi_job/jobs/archived/06dc027f.yaml`
- `rpi-job/rpi_job/jobs/archived/25f118bc.yaml`

## Performance Metrics

- `server_startup_seconds=1.966`
- `total_test_seconds=14.028`

## Conclusion

The core job-server workflow is working headlessly:
- server boots,
- jobs can be submitted,
- job YAML can be retrieved,
- async workers complete,
- concurrent jobs coexist,
- stop and archive endpoints respond.

But this is **not a perfect GREEN RUN** because of functional defects in:
- `latest` ordering,
- server-side prompt validation,
- stop/completion race consistency.
