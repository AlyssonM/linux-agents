#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/alyssonpi/.openclaw/workspace/linux-agents
SERVER_DIR="$ROOT/rpi-job"
CLIENT_DIR="$ROOT/rpi-client"
BASE_URL="http://127.0.0.1:7600"
PY_PATH="$SERVER_DIR:$CLIENT_DIR"
VENV_PY="$ROOT/.venv/bin/python"
ARTIFACT_DIR="$(pwd)"
SERVER_LOG="$ARTIFACT_DIR/server.log"
CLIENT_LOG="$ARTIFACT_DIR/client-commands.log"
JOB_IDS_FILE="$ARTIFACT_DIR/job_ids.txt"
METRICS="$ARTIFACT_DIR/metrics.txt"
: > "$CLIENT_LOG"
: > "$JOB_IDS_FILE"
: > "$METRICS"

run_client() {
  {
    echo ""
    echo "$ $(printf '%q ' "$@")"
    PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main "$@"
  } 2>&1 | tee -a "$CLIENT_LOG"
}

run_curl() {
  {
    echo ""
    echo "$ curl -sS $*"
    curl -sS "$@"
  } 2>&1 | tee -a "$CLIENT_LOG"
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

start_ts=$(date +%s.%N)
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_job.main > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$ARTIFACT_DIR/server.pid"
echo "server_pid=$SERVER_PID" | tee -a "$METRICS"

ready=0
for i in $(seq 1 50); do
  if curl -sS "$BASE_URL/jobs" > "$ARTIFACT_DIR/healthcheck.yaml" 2>/dev/null; then
    echo "server_ready_after_attempt=$i" | tee -a "$METRICS"
    ready=1
    break
  fi
  sleep 0.2
done
if [[ "$ready" -ne 1 ]]; then
  echo "Server did not become ready" | tee -a "$METRICS"
  exit 1
fi
ready_ts=$(date +%s.%N)
python3 - <<PY | tee -a "$METRICS"
start=$start_ts
ready=$ready_ts
print(f"server_startup_seconds={ready-start:.3f}")
PY

job1=$(PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main start "$BASE_URL" "job server e2e test")
echo "$job1" | tee "$ARTIFACT_DIR/job1-id.txt"
echo "$job1" >> "$JOB_IDS_FILE"
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main get "$BASE_URL" "$job1" | tee "$ARTIFACT_DIR/job1-get-initial.yaml"

for i in $(seq 1 20); do
  ts=$(date -Is)
  out=$(PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main get "$BASE_URL" "$job1")
  printf -- '---\npolled_at: %s\n%s\n' "$ts" "$out" >> "$ARTIFACT_DIR/job1-poll-history.yaml"
  status=$(printf '%s\n' "$out" | awk -F': ' '/^status:/{print $2; exit}')
  echo "job1_poll_$i=$status" | tee -a "$METRICS"
  if [[ "$status" == "done" || "$status" == "failed" || "$status" == "stopped" ]]; then
    printf '%s\n' "$out" > "$ARTIFACT_DIR/job1-get-final.yaml"
    break
  fi
  sleep 0.2
done

PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main list "$BASE_URL" | tee "$ARTIFACT_DIR/list-after-job1.yaml"
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main latest "$BASE_URL" -n 1 | tee "$ARTIFACT_DIR/latest-1.yaml"

job2=$(PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main start "$BASE_URL" "concurrent job alpha")
job3=$(PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main start "$BASE_URL" "concurrent job beta")
printf '%s\n%s\n' "$job2" "$job3" | tee "$ARTIFACT_DIR/concurrent-job-ids.txt"
printf '%s\n%s\n' "$job2" "$job3" >> "$JOB_IDS_FILE"

PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main stop "$BASE_URL" "$job2" | tee "$ARTIFACT_DIR/job2-stop.txt"

for job in "$job2" "$job3"; do
  for i in $(seq 1 20); do
    ts=$(date -Is)
    out=$(PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main get "$BASE_URL" "$job")
    printf -- '---\npolled_at: %s\n%s\n' "$ts" "$out" >> "$ARTIFACT_DIR/${job}-poll-history.yaml"
    status=$(printf '%s\n' "$out" | awk -F': ' '/^status:/{print $2; exit}')
    echo "${job}_poll_$i=$status" | tee -a "$METRICS"
    if [[ "$status" == "done" || "$status" == "failed" || "$status" == "stopped" ]]; then
      printf '%s\n' "$out" > "$ARTIFACT_DIR/${job}-final.yaml"
      break
    fi
    sleep 0.2
  done
done

PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main list "$BASE_URL" | tee "$ARTIFACT_DIR/list-after-concurrency.yaml"
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main latest "$BASE_URL" -n 3 | tee "$ARTIFACT_DIR/latest-3.yaml"

(run_client get "$BASE_URL" doesnotexist || true) | tee "$ARTIFACT_DIR/error-get-missing.txt"
(run_curl -X POST "$BASE_URL/job" -H 'content-type: application/json' -d '{"prompt":"   "}' || true) | tee "$ARTIFACT_DIR/error-empty-prompt.txt"

run_curl -X POST "$BASE_URL/jobs/clear" | tee "$ARTIFACT_DIR/clear-jobs.json"
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main list "$BASE_URL" | tee "$ARTIFACT_DIR/list-after-clear.yaml"
PYTHONPATH="$PY_PATH" "$VENV_PY" -m rpi_client.main list "$BASE_URL" --archived | tee "$ARTIFACT_DIR/list-archived.yaml"

SERVER_JOBS_DIR="$SERVER_DIR/rpi_job/jobs"
find "$SERVER_JOBS_DIR" -maxdepth 2 -type f -name '*.yaml' -print | sort > "$ARTIFACT_DIR/server-yaml-paths.txt"

end_ts=$(date +%s.%N)
python3 - <<PY | tee -a "$METRICS"
start=$start_ts
end=$end_ts
print(f"total_test_seconds={end-start:.3f}")
PY
