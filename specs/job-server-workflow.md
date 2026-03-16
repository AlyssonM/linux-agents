# Job Server End-to-End Workflow

## Instructions
- As you work, keep track of your notes in a text editor or markdown file.
- If you work longer than 10 minutes from your start time, wrap up and record partial results.
- Save server logs, client output, and returned job YAML for every run.
- Use the default local endpoint unless a different host or port is under test: `http://127.0.0.1:7600`.

## Requirements
- Python environment with `rpi-job` and `rpi-client` installed
- Local port `7600` available or a documented alternative
- Ability to keep the FastAPI server running during the full test

## Tasks
- [ ] Start the job server: `python -m rpi_job.main` or `uvicorn rpi_job.main:app --host 0.0.0.0 --port 7600`.
- [ ] Verify the server is reachable.
- [ ] Submit a job via `rpi-client start http://127.0.0.1:7600 "job server e2e test"`.
- [ ] Record the returned `job_id`.
- [ ] Fetch the job with `rpi-client get http://127.0.0.1:7600 <job_id>`.
- [ ] Poll the job state by repeating `get` until it reaches a terminal state or a timeout threshold is hit.
- [ ] Run `rpi-client list http://127.0.0.1:7600` and verify the job appears.
- [ ] Run `rpi-client latest http://127.0.0.1:7600 -n 1` and verify the newest job is returned.
- [ ] Verify the corresponding YAML file exists under the server jobs directory.
- [ ] Submit at least two additional jobs in quick succession to test concurrent handling.
- [ ] Verify `list` includes all active or completed jobs.
- [ ] Retrieve each concurrent job and compare status progression.
- [ ] Stop one active job with `rpi-client stop http://127.0.0.1:7600 <job_id>` if applicable.
- [ ] Verify stopped jobs move to `stopped` and completed jobs retain results.
- [ ] If supported by the test plan for that run, archive/clear completed jobs and verify list behavior before and after archival.

## Expected Outputs
- Server startup without fatal exception
- `start` returns a job id
- `get` returns YAML for the target job
- `list` returns all visible jobs
- `latest` returns the newest jobs requested
- Multiple jobs can coexist without corrupting status files
- `stop` updates job status correctly

## Deliverables
- A report containing:
  - server launch command and log path
  - all submitted job ids
  - status progression for each job
  - output from `list`, `latest`, `get`, and `stop`
  - paths to YAML job artifacts
  - concurrency observations, race conditions, or file-locking issues
  - final pass/fail/skip matrix

## Known Issues / Limitations
- Job completion timing may vary on Raspberry Pi due to CPU and storage performance.
- YAML job files are file-backed state; concurrent access should be observed for partial writes or stale reads.
- If worker processes exit early, job state may show `failed` or remain incomplete; record exact evidence.
- Long polling should use a reasonable timeout to avoid hanging the test run indefinitely.
