# ✅ Fix Aplicado: Captura de tmux output

## Status

**Implementado ✅ | Testando ⏳**

## O que foi feito

### 1. Código atualizado

Arquivo: `listen/worker.py`

Adicionada captura de tmux para opencode/openclaw:

```python
elif agent in ["opencode", "openclaw"] and _session_exists(session_name):
    captured = _capture_pane(session_name)
    lines = []

    for line in captured.split('\n'):
        line = line.rstrip()
        if not line or SENTINEL_PREFIX in line:
            continue
        if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@', '/']):
            continue
        lines.append(line)

    if lines:
        data["summary"] = '\n'.join(lines[-20:])[:4000]
```

### 2. Commit

```
3299482 fix: capture tmux output for opencode/openclaw summary
```

### 3. Serviço reiniciado

```
Active: active (running)
Main PID: 173035
```

### 4. Teste em andamento

Job `74d2cf22`: `ping` via opencode

Aguardando conclusão...

## Como testar

```bash
# Criar job
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say TEST", "agent": "opencode"}'

# Ver resultado
curl http://localhost:7600/job/<JOB_ID> | grep summary
```

## Esperado

### Antes:
```yaml
summary: ''  # ❌
```

### Depois:
```yaml
summary: 'TEST'  # ✅
```

## Documentação

- **SUMMARY-FIX.md** - Solução completa
- **FIX-APPLIED.md** - Implementação
- **FIX-TEST.md** - Este arquivo

## Próximo

Aguardar job 74d2cf22 completar e verificar summary.
