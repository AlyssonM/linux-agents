# listen - Job Server (port 7600)

Multi-agent job server supporting **codex** and **opencode**.

## Agents

| Agent | Status | Notes |
|-------|--------|-------|
| **codex** | ⚠️ API limited | OpenAI reset until Mar 18, 2026 |
| **claude** | ✅ Available | Alias for opencode |
| **opencode** | ✅ Working | **Recommended** |

## Usage

```bash
# Start server
cd ~/Github/linux-agents
.venv/bin/python listen/main.py

# Submit job
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "minha tarefa", "agent": "opencode"}'

# Check job
curl http://localhost:7600/job/<job_id>

# List jobs
curl http://localhost:7600/jobs
```

## Systemd Service

```bash
systemctl --user start linux-agents-listen
systemctl --user status linux-agents-listen
```

## Related

- **openclaw-listen** (port 7610) - Dedicated OpenClaw agent server
- **AGENTS.md** - Detailed agent documentation
- **DEBUG.md** - Debug notes and troubleshooting
