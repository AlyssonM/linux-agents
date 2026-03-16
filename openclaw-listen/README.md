# openclaw-listen

OpenClaw-native async job listener for `linux-agents`.

This component is complementary to `listen/`:

- `listen/` = external agent CLI runtime (Codex-centric today)
- `openclaw-listen/` = OpenClaw-native runtime using `openclaw agent`

## What it does

- accepts jobs over HTTP
- stores job state in YAML
- spawns an async worker per job
- runs work through the local OpenClaw runtime
- optionally delivers friendly responses back to chat channels via OpenClaw delivery

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

## Notes

v1 is intentionally pragmatic:

- YAML-backed storage
- async subprocess worker model
- execution via local `openclaw agent`
- explicit metadata for source and delivery
- simple strategy resolution

It is not trying to replace OpenClaw gateway or distributed orchestration.
