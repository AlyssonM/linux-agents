# Fix em progresso: Debug logging adicionado

## Mudança

Adicionado debug logging no `worker.py`:

```python
# Log agent, prompt, model
debug_log = Path("/tmp/worker-debug.log")
with open(debug_log, "a") as f:
    f.write(f"[{job_id}] agent={agent}, prompt={prompt}, model={model}\n")
```

## Objetivo

Descobrir qual agent o worker está recebendo:
- Se `agent=opencode`: problema está no AGENT_RUNNERS
- Se `agent=codex`: problema está no main.py (não está passando)
- Se vazio ou missing: argv[3] não está sendo lido

## Como verificar

```bash
# Criar job
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ping", "agent": "opencode"}'

# Ver debug log
cat /tmp/worker-debug.log | tail -1
```

## Esperado

```bash
[<job_id>] agent=opencode, prompt=ping, model=
```

## Status

⏳ **Aguardando serviço iniciar**
⏳ **Aguardando resultado do teste**

## Próximo passo

Dependendo do log:
1. Se `agent=opencode`: debug AGENT_RUNNERS
2. Se `agent=codex` ou vazio: debug main.py
3. Se não houver log: worker não está sendo chamado
