# listen

High-level REST job server used by the Linux Agents stack on port `7600`.

## What It Does

- accepts jobs over HTTP
- stores job state in YAML files under `apps/listen/jobs/`
- spawns workers to execute prompts via configured agent runtimes
- exposes endpoints to create, inspect, list, archive, and stop jobs

## API

- `POST /job`
- `POST /job/upload`
- `GET /job/{id}`
- `GET /jobs`
- `POST /jobs/clear`
- `DELETE /job/{id}`

### `POST /job` payload

```json
{
  "prompt": "required string",
  "agent": "codex | openclaw | opencode | pi | claude",
  "model": "optional provider/model string",
  "timeout_seconds": 900,
  "api_key": "optional raw key value",
  "api_key_env": "optional env var name, e.g. OPENAI_API_KEY",
  "image_attachments": ["optional image path or URL", "optional image path or URL"]
}
```

- `api_key` is injected only into the worker process.
- `image_attachments` is appended to prompt context and passed to the selected agent.
- if `api_key` is set and `api_key_env` is omitted, the server infers env name from model provider:
  - `openai/gpt-4.1` → `OPENAI_API_KEY`
  - `anthropic/claude-sonnet-4` → `ANTHROPIC_API_KEY`
  - `openrouter/openai/gpt-4o-mini` → `OPENROUTER_API_KEY`

### `POST /job/upload` (multipart form-data)

Accepted form fields:
- `prompt` (required)
- `agent` (optional)
- `model` (optional)
- `api_key` (optional)
- `api_key_env` (optional)
- `image_attachments` (optional, repeatable for URL/path entries)
- `image_files` (optional, repeatable image uploads)

Uploaded files are persisted under `apps/listen/jobs/uploads/<job_id>/`.

## Run

```bash
cd apps/listen
uv run python main.py
```

## Example Requests

```bash
# 1) Create a basic job (default agent=codex)
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt":"write a shell script to monitor CPU and memory"}'

# 2) Create a job selecting agent + model
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"generate a docker-compose for redis + postgres",
    "agent":"opencode",
    "model":"openrouter/openai/gpt-4o-mini"
  }'

# 2b) Create a multimodal job with image attachments
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"analyze these screenshots and summarize the issue",
    "agent":"pi",
    "model":"openrouter/openai/gpt-4o-mini",
    "image_attachments":[
      "/home/alyssonpi/screenshots/error-1.png",
      "https://example.com/diagram.png"
    ]
  }'

# 3) Create a Pi job with explicit API key env
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"refactor this project to use typed settings",
    "agent":"pi",
    "model":"openai/gpt-4.1:medium",
    "api_key_env":"OPENAI_API_KEY",
    "api_key":"sk-..."
  }'

# 4) Upload images from another machine using multipart
curl -X POST http://127.0.0.1:7600/job/upload \
  -F 'prompt=analyze the attached screenshot and explain root cause' \
  -F 'agent=pi' \
  -F 'model=openrouter/openai/gpt-4o-mini' \
  -F 'image_files=@/home/user/captura.png' \
  -F 'image_files=@/home/user/fluxo.jpg'

# 5) Create a job and let listen infer API key env from model provider
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write tests for auth middleware",
    "agent":"pi",
    "model":"anthropic/claude-sonnet-4",
    "api_key":"sk-ant-..."
  }'

# 6) Inspect one job
curl http://127.0.0.1:7600/job/<job_id>

# 7) List running/non-archived jobs
curl http://127.0.0.1:7600/jobs

# 8) List archived jobs
curl "http://127.0.0.1:7600/jobs?archived=true"

# 9) Archive all active jobs
curl -X POST http://127.0.0.1:7600/jobs/clear

# 10) Stop one running job
curl -X DELETE http://127.0.0.1:7600/job/<job_id>
```

Use examples with `"api_key":"..."` only for manual human testing.
For agentic flows, do not send `api_key` in the payload.

## Agentic-safe without api_key in payload

Start the server with secrets injected into the environment:

```bash
cd apps/listen
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
uv run python main.py
```

Then create jobs without `api_key` and without `api_key_env`:

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write a small motivation quote",
    "agent":"pi",
    "model":"openrouter/openai/gpt-oss-20b"
  }'
```

## Agentic-safe with systemd (persistent service)

If `listen` runs as a service (`linux-agents-listen.service`), first confirm which manager is active.
Avoid keeping both units (user and system) active at the same time on the same port.

```bash
systemctl --user cat linux-agents-listen.service
sudo systemctl cat linux-agents-listen.service
ps -ef | grep '/apps/listen/main.py' | grep -v grep
```

If the active service is the system service (`/etc/systemd/system/linux-agents-listen.service`), inject into the system manager and restart:

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENROUTER_API_KEY="$OPENROUTER_API_KEY"'

sudo systemctl restart linux-agents-listen.service
sudo systemctl status linux-agents-listen.service --no-pager -n 30
```

If the active service is the user service, use `systemctl --user set-environment` and `systemctl --user restart`.

Then submit jobs without a key in the payload:

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write a small motivation quote",
    "agent":"pi",
    "model":"openrouter/openai/gpt-oss-20b"
  }'
```

When you need to switch to a new key, run the same `set-environment` with the new secret and restart the service.

You do not need to re-inject on every provider switch if all required keys are already loaded in the service.
Re-injection is only required when:
- a new provider is introduced and not yet loaded
- a key rotation happens

Example loading OpenRouter + OpenAI and restarting only once:

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENROUTER_API_KEY="$OPENROUTER_API_KEY"'

SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENAI_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENAI_API_KEY="$OPENAI_API_KEY"'

sudo systemctl restart linux-agents-listen.service
```

If the job fails with `No API key found for openrouter` after this flow, `curl` is usually hitting another `listen` process (outside this service).
Validate:

```bash
sudo systemctl cat linux-agents-listen.service
ps -ef | grep '/apps/listen/main.py' | grep -v grep
```

Ensure there is only one server on port `7600`, and that it is the same service process that received `set-environment`.

### Agentic mode with `api_key` in payload (not recommended)

It works, including after worker-side sanitization, but it still has higher operational risk.

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'curl -sS -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"write a small motivation quote\",\"agent\":\"pi\",\"model\":\"openrouter/openai/gpt-oss-20b\",\"api_key_env\":\"OPENROUTER_API_KEY\",\"api_key\":\"$OPENROUTER_API_KEY\"}"'
```

Main risks of this format:
- the key may appear in shell history and terminal telemetry
- the key may leak in proxy/reverse-proxy logs before reaching the worker
- the key may be captured by HTTP observability tools in transit

Recommendation: prefer `set-environment` in systemd and submit `/job` without `api_key` in JSON.

## Using shell env vars for safer curl usage

Manual human usage:

```bash
LISTEN_URL="http://127.0.0.1:7600"
OPENAI_API_KEY="sk-..."

curl -X POST "$LISTEN_URL/job" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\":\"implement health check endpoint\",
    \"agent\":\"pi\",
    \"model\":\"openai/gpt-4.1\",
    \"api_key\":\"$OPENAI_API_KEY\"
  }"
```

## Response examples

```bash
# POST /job
# {"job_id":"a1b2c3d4","status":"running"}

# DELETE /job/{id}
# {"job_id":"a1b2c3d4","status":"stopped"}
```

## Notes on agents and model strings

- `codex`: model is passed via `codex exec -c model='<model>'`
- `opencode`: model is passed via `opencode run ... --model <model>`
- `openclaw` and `claude`: model is passed via `openclaw agent --model '<model>'`
- `pi`: supports `provider/model` and optional thinking suffix (`:off|minimal|low|medium|high|xhigh`)
- for `pi`, `openai/gpt-4.1:medium` becomes:
  - model: `openai/gpt-4.1`
  - thinking: `medium`

## Companion CLI

```bash
uv run rpi-client start http://127.0.0.1:7600 "my task" --agent opencode
```

## Related Components

- `rpi-client` is the primary CLI client for this server
- `rpi-job` is a simpler job-server implementation
- `openclaw-listen` is the OpenClaw-focused listener variant
