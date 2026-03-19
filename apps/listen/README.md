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

### `POST /job` payload

```json
{
  "prompt": "required string",
  "agent": "codex | openclaw | opencode | pi | claude",
  "model": "optional provider/model string",
  "timeout_seconds": 900,
  "api_key": "optional raw key value",
  "api_key_env": "optional env var name, e.g. OPENAI_API_KEY"
}
```

- `api_key` is injected only into the worker process.
- if `api_key` is set and `api_key_env` is omitted, the server infers env name from model provider:
  - `openai/gpt-4.1` → `OPENAI_API_KEY`
  - `anthropic/claude-sonnet-4` → `ANTHROPIC_API_KEY`
  - `openrouter/openai/gpt-4o-mini` → `OPENROUTER_API_KEY`

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

# 4) Create a job and let listen infer API key env from model provider
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write tests for auth middleware",
    "agent":"pi",
    "model":"anthropic/claude-sonnet-4",
    "api_key":"sk-ant-..."
  }'

# 5) Inspect one job
curl http://127.0.0.1:7600/job/<job_id>

# 6) List running/non-archived jobs
curl http://127.0.0.1:7600/jobs

# 7) List archived jobs
curl "http://127.0.0.1:7600/jobs?archived=true"

# 8) Archive all active jobs
curl -X POST http://127.0.0.1:7600/jobs/clear

# 9) Stop one running job
curl -X DELETE http://127.0.0.1:7600/job/<job_id>
```

Use os exemplos com `"api_key":"..."` apenas para teste manual por humano.
Para fluxo agêntico, não envie `api_key` no payload.

## Agentic-safe sem api_key no payload

Suba o servidor com segredos injetados no ambiente:

```bash
cd apps/listen
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
uv run python main.py
```

Depois crie jobs sem `api_key` e sem `api_key_env`:

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write a small motivation quote",
    "agent":"pi",
    "model":"openrouter/openai/gpt-oss-20b"
  }'
```

## Agentic-safe com systemd (serviço persistente)

Se o `listen` roda como serviço (`linux-agents-listen.service`), primeiro confirme qual manager está ativo.
Evite manter as duas units (user e system) ao mesmo tempo com a mesma porta.

```bash
systemctl --user cat linux-agents-listen.service
sudo systemctl cat linux-agents-listen.service
ps -ef | grep '/apps/listen/main.py' | grep -v grep
```

Se o serviço ativo for o system service (`/etc/systemd/system/linux-agents-listen.service`), injete no manager do sistema e reinicie:

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENROUTER_API_KEY="$OPENROUTER_API_KEY"'

sudo systemctl restart linux-agents-listen.service
sudo systemctl status linux-agents-listen.service --no-pager -n 30
```

Se o serviço ativo for o user service, use `systemctl --user set-environment` e `systemctl --user restart`.

Depois envie jobs sem chave no payload:

```bash
curl -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"write a small motivation quote",
    "agent":"pi",
    "model":"openrouter/openai/gpt-oss-20b"
  }'
```

Quando quiser trocar para uma nova chave, rode o mesmo `set-environment` com a nova secret e reinicie o serviço.

Você não precisa reinjetar a cada troca de provider se já carregar todas as chaves necessárias no serviço.
Reinjetar só é necessário quando:
- entrar um provider novo ainda não carregado
- houver rotação de chave

Exemplo carregando OpenRouter + OpenAI e reiniciando uma única vez:

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENROUTER_API_KEY="$OPENROUTER_API_KEY"'

SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENAI_API_KEY -- \
bash -lc 'sudo systemctl set-environment OPENAI_API_KEY="$OPENAI_API_KEY"'

sudo systemctl restart linux-agents-listen.service
```

Se o job falhar com `No API key found for openrouter` após esse fluxo, normalmente o `curl` está batendo em outro processo `listen` (fora desse service).
Valide:

```bash
sudo systemctl cat linux-agents-listen.service
ps -ef | grep '/apps/listen/main.py' | grep -v grep
```

Garanta que exista apenas um servidor na porta `7600` e que ele seja o mesmo processo do service que recebeu `set-environment`.

### Modo agentic com `api_key` no payload (não recomendado)

Funciona, inclusive após a sanitização do worker, mas ainda é um caminho com risco operacional maior.

```bash
SECRETCTL_PASSWORD="$(pass show secretctl/master-password)" \
python3 ~/.pi/skills/secretctl/scripts/wrapper_secretctl.py run -k OPENROUTER_API_KEY -- \
bash -lc 'curl -sS -X POST http://127.0.0.1:7600/job \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"write a small motivation quote\",\"agent\":\"pi\",\"model\":\"openrouter/openai/gpt-oss-20b\",\"api_key_env\":\"OPENROUTER_API_KEY\",\"api_key\":\"$OPENROUTER_API_KEY\"}"'
```

Riscos principais desse formato:
- a chave pode aparecer em histórico de shell e telemetria de terminal
- a chave pode vazar em logs de proxy/reverse-proxy antes de chegar no worker
- a chave pode ser capturada por ferramentas de observabilidade HTTP no caminho

Recomendação: preferir `set-environment` no systemd e enviar `/job` sem `api_key` no JSON.

## Using shell env vars for safer curl usage

Uso manual por humano:

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
uv run rpi-client start http://127.0.0.1:7600 "minha tarefa" --agent opencode
```

## Related Components

- `rpi-client` is the primary CLI client for this server
- `rpi-job` is a simpler job-server implementation
- `openclaw-listen` is the OpenClaw-focused listener variant
