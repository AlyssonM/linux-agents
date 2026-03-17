# Resumo: Summary vazio em jobs opencode

## Caso real

```yaml
id: f84c3a19
prompt: ping
agent: opencode
status: completed
exit_code: 0
summary: ''  # ❌ DEVERIA MOSTRAR "pong"
```

## Problema

**✅ SIM, deveria mostrar a resposta no summary!**

O `_run_opencode()` não captura o output do tmux.

## Por que acontece

| Agent | Output capture | Summary |
|-------|----------------|---------|
| **codex** | Arquivo `-o output.txt` | ✅ Funciona |
| **opencode** | Nenhum | ❌ Vazio |

## Solução rápida

Adicionar no `finally` de `worker.py`:

```python
elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
    captured = _capture_pane(session_name)
    lines = [l for l in captured.split('\n')
             if SENTINEL_PREFIX not in l and
                 not l.strip().startswith(('$', '>', '/')) and
                 l.strip()]
    data["summary"] = '\n'.join(lines[-20:])[:4000]
```

## Documentação completa

- **`SUMMARY-FIX.md`** - Solução completa com código
- **`SUMMARY-EMPTY.md`** - Explicação do problema

## Status

⏳ **Bug documentado, aguardando implementação**
