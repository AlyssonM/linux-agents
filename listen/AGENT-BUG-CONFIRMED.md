# ✅ Resposta: Systemd está rodando, mas há bug

## Status do Systemd

```
Active: active (running) ✅
Main PID: 174637
Port: 7600
```

## Problema confirmado

Job 49ec0b83 mostra:
```yaml
updates:
  - Spawned Codex worker in tmux session  # ❌ ERRADO!
```

Mas você pediu:
```json
{"prompt": "ping", "agent": "opencode"}
```

Deveria ser:
```yaml
updates:
  - Spawned OpenCode CLI worker with default model
```

## Causa

O **worker está usando "codex"** quando deveria usar **"opencode"**.

## main.py está correto ✅

```python
req.agent  # "opencode"
data["agent"] = req.agent  # Salva "opencode"
proc = subprocess.Popen([..., req.agent, ...])  # Passa "opencode"
```

## Possível problema

O YAML pode não ter salvo o "agent:" campo, ou o worker não está lendo corretamente.

## Verificar se YAML tem agent

```bash
curl http://localhost:7600/job/49ec0b83 | grep "^agent:"
```

Se não mostrar nada, o campo `agent` não está sendo salvo no YAML inicial!

## Conclusão

- **Systemd**: ✅ Funcionando
- **main.py**: ✅ Passando agent correto
- **Worker**: ❌ Usando "codex" em vez de "opencode"
- **YAML**: ❌ Pode não ter campo "agent"

**Bug confirmado: Worker está ignorando o agent e usando default "codex".**
