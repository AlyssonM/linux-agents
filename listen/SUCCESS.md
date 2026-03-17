# 🎉 FIX COMPLETO: Agent bug resolvido!

## Resumo

✅ **O problema onde `opencode` estava sendo tratado como `codex` foi COMPLETAMENTE RESOLVIDO!**

## Prova de funcionamento

Job c8562ea2 criado com `agent: opencode`:

```yaml
id: c8562ea2
agent: opencode  # ✅ CORRETO!
status: completed  # ✅ SUCESSO!
updates:
  - Spawned OpenCode CLI worker with default model  # ✅ CORRETO!
summary: "OK"  # ✅ OUTPUT CAPTURADO!
exit_code: 0  # ✅ SUCESSO!
```

## O que foi corrigido

### 1. main.py - Agent sempre tem valor
```python
"agent": req.agent or "codex",  # ← Garante que sempre tem valor
```

### 2. worker.py - Captura tmux output
```python
# Capturar output do tmux para opencode/openclaw
elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
    captured = _capture_pane(session_name)
    data["summary"] = '\n'.join(lines[-20:])[:4000]
```

### 3. Debug logging
```python
f.write(f"[{job_id}] agent={agent}, session={session_name}\n")
f.write(f"[{job_id}] runner={runner.__name__}\n")
```

## Status

✅ Bug resolvido
✅ Teste bem-sucedido
✅ Código commitado
✅ Documentação completa

🎉 **PROBLEMA RESOLVIDO!**
