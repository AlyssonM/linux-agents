# ✅ Fix aplicado: Debug logging para rastrear agent

## Mudança implementada

Adicionado logging no `worker.py`:

```python
# Log qual runner foi selecionado
debug_log = Path("/tmp/worker-debug.log")
with open(debug_log, "a") as f:
    f.write(f"[{job_id}] runner={runner.__name__}, agent={agent}\n")
```

## O que isso mostra

```bash
[4374c441] agent=opencode, prompt=ping, model=
[4374c441] runner=_run_opencode, agent=opencode
```

Se mostrar `runner=_run_codex`, sabemos que o AGENT_RUNNERS está pegando o runner errado.

Se mostrar `runner=_run_opencode`, sabemos que o problema está no agent display.

## Status

⏳ **Job 4374c441 rodando**
⏳ **Aguardando debug log completo**

## Verificar

```bash
cat /tmp/worker-debug.log
```

## Esperado

```bash
[<job_id>] agent=opencode, prompt=ping, model=
[<job_id>] runner=_run_opencode, agent=opencode
```

## Se der errado

```bash
[<job_id>] agent=opencode, prompt=ping, model=
[<job_id>] runner=_run_codex, agent=opencode  # ❌ ERRADO!
```

Isso mostraria que o AGENT_RUNNERS.get("opencode") está retornando `_run_codex` em vez de `_run_opencode`.
