# ✅ ANÁLISE FINAL: Encontrei o BUG!

## AGENT_RUNNERS NO worker.py

```python
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,  # ❌ claude → _run_openclaw
    "openclaw": _run_openclaw,  # ❌ openclaw → _run_openclaw
    "opencode": _run_opencode,  # ✅ opencode → _run_opencode
}
```

## Funções existentes

```bash
grep -n "def _run_opencode" worker.py
# 116:def _run_opencode(job_id: str, prompt: str, model: str, session_name: str) -> int:
```

✅ **_run_opencode existe!**

## Então qual é o problema?

O YAML mostra "Spawned Codex worker", mas agent="opencode".

Isso significa que o **agent_display** está errado!

## Verificar o agent_display

```python
if agent == "claude":
    agent_display = "OpenCode (claude compatibility mode)"
elif agent == "openclaw":
    agent_display = "OpenClaw agent CLI"
elif agent == "opencode":
    agent_display = "OpenCode CLI"  # ← DEVERIA usar este!
else:
    agent_display = f"{agent.capitalize()}"  # ← Mas está usando este?
```

Se por algum motivo o agent não for exatamente "opencode", ele vai para o `else`:

```python
agent_display = f"{agent.capitalize()}"  # "Codex" se for "codex"
```

## Possível problema

O agent pode estar sendo modificado ou chegado como "codex" em vez de "opencode".

## Verificar com novo debug

Agora temos logging ANTES e DEPOIS do AGENT_RUNNERS.get():

```python
f.write(f"[{job_id}] agent={agent}, session={session_name}\n")
runner = AGENT_RUNNERS.get(agent)
f.write(f"[{job_id}] runner={runner.__name__}\n")
```

Isso vai mostrar exatamente qual agent está sendo usado.

## Aguardando job 9b8e89d0 completar

```bash
cat /tmp/worker-debug.log | tail -10
```

## Status

✅ **AGENT_RUNNERS tem "opencode"**
✅ **_run_opencode existe**
⏳ **Aguardando debug log do job atual**
