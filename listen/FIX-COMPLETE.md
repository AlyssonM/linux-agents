# 🎉 FIX COMPLETO: Agent bug resolvido!

## Resumo

O problema onde `opencode` estava sendo tratado como `codex` foi **COMPLETAMENTE RESOLVIDO**!

## Causa raiz

O campo `agent` não estava sendo escrito no YAML inicial quando era `None`, fazendo o worker usar o default "codex".

## Solução aplicada

### 1. main.py - Garantir agent sempre tem valor
```python
"agent": req.agent or "codex",
```

### 2. worker.py - Capturar tmux output
```python
# Capturar output do tmux para opencode/openclaw
if agent in ["opencode", "openclaw"] and _session_exists(session_name):
    captured = _capture_pane(session_name)
    # Filtrar linhas úteis
    data["summary"] = '\n'.join(lines[-20:])[:4000]
```

### 3. Debug logging
```python
f.write(f"[{job_id}] agent={agent}, session={session_name}\n")
f.write(f"[{job_id}] runner={runner.__name__}\n")
```

## Resultado do teste (Job c8562ea2)

```yaml
id: c8562ea2
agent: opencode  # ✅ CORRETO!
status: completed  # ✅ SUCESSO!
prompt: echo OK
updates:
  - Spawned OpenCode CLI worker with default model  # ✅ CORRETO!
summary: |
  OK  # ✅ OUTPUT CAPTURADO!
exit_code: 0  # ✅ SUCESSO!
duration_seconds: 16
completed_at: '2026-03-17T05:56:21Z'
```

## Antes vs Depois

| Item | Antes | Depois |
|------|-------|--------|
| **Agent no YAML** | ❌ Campo faltando | ✅ `agent: opencode` |
| **Runner usado** | ❌ Codex worker | ✅ OpenCode CLI worker |
| **Summary** | ❌ Vazio | ✅ "OK" |
| **Exit code** | ❌ 1 (falha) | ✅ 0 (sucesso) |
| **Output capturado** | ❌ Não | ✅ Sim (tmux) |

## Commits principais

- `3299482` - Fix: capture tmux output for opencode/openclaw summary
- `7cf0f6e` - Fix: add debug logging to worker.py
- `main.py` - Fix: ensure agent field always has value in YAML

## Documentação criada

- **SUMMARY-FIX.md** - Solução técnica completa
- **FIX-APPLIED.md** - Implementação do fix
- **FIX-FINAL.md** - Confirmação do sucesso
- Vários arquivos de debug e diagnóstico

## Como testar

```bash
# Criar job
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello", "agent": "opencode"}'

# Ver resultado
curl http://localhost:7600/job/<job_id>
```

## Status

✅ **Bug resolvido**
✅ **Teste bem-sucedido**
✅ **Código commitado**
✅ **Documentação completa**
