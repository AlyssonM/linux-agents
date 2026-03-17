# ✅ Fix aplicado: Debug logging melhorado

## Mudança

Movido o debug log para ANTES da operação que pode falhar:

```python
# ANTES (podia falhar antes):
f.write(f"[{job_id}] agent={agent}, ...")
runner = AGENT_RUNNERS.get(agent)  # ← Falha aqui?
f.write(f"[{job_id}] runner={runner.__name__}, ...")

# DEPOIS (captura o erro):
f.write(f"[{job_id}] agent={agent}, session={session_name}\n")
runner = AGENT_RUNNERS.get(agent)
if not runner:
    f.write(f"[{job_id}] ERROR: runner=None\n")  # ← Captura o erro!
f.write(f"[{job_id}] runner={runner.__name__}\n")
```

## O que isso mostra

Agora vamos ver EXATAMENTE onde está falhando:
- Se mostrar `runner=None`: AGENT_RUNNERS.get() está falhando
- Se mostrar `runner=_run_opencode`: Problema está depois
- Se não mostrar nada: Está falhando antes

## Teste em andamento

Job criado, aguardando debug log.

## Verificar

```bash
cat /tmp/worker-debug.log | tail -10
```

## Esperado

```bash
[<job_id>] agent=opencode, session=job-<id>
[<job_id>] runner=_run_opencode
```

## Se der erro

```bash
[<job_id>] agent=opencode, session=job-<id>
[<job_id>] ERROR: runner=None for agent=opencode
```

Isso mostraria que AGENT_RUNNERS.get("opencode") está retornando None!

## Status

✅ **Debug logging melhorado**
✅ **Servidor reiniciado**
⏳ **Teste em andamento**
