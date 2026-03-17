# ✅ Debug revela: agent está sendo passado CORRETAMENTE!

## Evidência

```
[e2af7505] agent=opencode, prompt=ping, model=
```

**O agent "opencode" está sendo recebido pelo worker!** ✅

## Então onde está o bug?

O worker está recebendo `agent=opencode`, mas o YAML mostra "Codex worker".

Isso significa que o problema está no **AGENT_RUNNERS** ou no **agent display**.

## Verificar AGENT_RUNNERS

```python
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,  # ✅ Existe!
}
```

## Possível problema

O agent display pode estar errado:

```python
if agent == "claude":
    agent_display = "OpenCode (claude compatibility mode)"
elif agent == "openclaw":
    agent_display = "OpenClaw agent CLI"
elif agent == "opencode":
    agent_display = "OpenCode CLI"
else:
    agent_display = f"{agent.capitalize()}"  # <--- CULPADO?
```

Se o agent não for "opencode" por algum motivo, ele vai para o `else` e usa `capitalize()`.

## Verificar

```bash
curl http://localhost:7600/job/e2af7505
```

## Status

✅ **Debug funcionando**
✅ **Agent sendo passado corretamente**
⏳ **Verificando por que mostra "Codex worker"**
