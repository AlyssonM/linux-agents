# openclaw-listen

OpenClaw-native async job listener for `linux-agents`.

This component is complementary to the existing job-server flows:

- `rpi-job/` = simple generic subprocess shell jobs
- `listen/` = external agent CLI runtime (`codex exec` + tmux)
- `openclaw-listen/` = OpenClaw-native runtime via `openclaw agent`

## What it does

- accepts jobs over HTTP
- stores job state in YAML
- spawns an async worker per job
- runs work through the local OpenClaw runtime (`openclaw agent --agent main --local` by default)
- optionally delivers friendly responses back to a chat channel/target via OpenClaw delivery

## Current v1 behavior

- `execution.strategy=auto` resolves to `acp`
- `inline` and `subagent` are currently normalized onto the ACP-backed runner in v2
- `acp` is the native execution path for this component
- cancellation is best-effort and currently targets the worker process
- delivery uses OpenClaw's `--reply-channel` and `--reply-to` flags; `delivery.reply_to` is stored as metadata only for now

## Run

```bash
cd openclaw-listen
python main.py
```

or:

```bash
uvicorn main:app --host 0.0.0.0 --port 7610
```

## API

- `POST /jobs` — create a job
- `GET /jobs/{id}` — get full YAML job
- `GET /jobs` — list jobs summary
- `POST /jobs/clear` — archive all jobs
- `POST /jobs/{id}/cancel` — best-effort cancellation

`POST /jobs` returns HTTP `202` with both `id` and `job_id`, plus `status_url`, to stay convenient for machines and humans.

`GET /jobs` supports a small set of filters in v1:

- `archived=true`
- `status=<queued|planning|running|succeeded|failed|cancelled>`
- `source_type=<rest|direct|telegram|discord|gateway>`

## Example payload

```json
{
  "instruction": "Abra o Chromium e me diga o que está aberto na tela",
  "execution": { "strategy": "auto", "timeout_seconds": 900 },
  "source": { "type": "rest" },
  "delivery": { "mode": "poll", "send_result": false }
}
```

## Delivery example (Telegram)

```json
{
  "instruction": "Resuma o status atual",
  "source": {
    "type": "telegram",
    "channel": "telegram",
    "chat_id": "1129943309",
    "message_id": "123"
  },
  "delivery": {
    "mode": "reply",
    "send_result": true,
    "channel": "telegram",
    "target": "1129943309",
    "reply_to": "123"
  }
}
```

In the current CLI integration, `target` is what maps to OpenClaw's `--reply-to` destination override. `reply_to` remains useful metadata for future channel-specific reply threading.

## Requirements

- `openclaw` CLI installed and working locally
- local model/runtime configuration available for `openclaw agent --local`
- network access if the configured model provider needs it

## Notes

v1 is intentionally pragmatic:

- YAML-backed storage
- async subprocess worker model
- execution via a per-job ACP subprocess and isolated session key
- explicit metadata for source and delivery
- simple strategy resolution

It is not trying to replace OpenClaw gateway or distributed orchestration.
