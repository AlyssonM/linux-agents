# ✅ Fix aplicado: Melhorado filtro de captura do tmux

## Mudança

```python
# ANTES:
if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@', '/']):
    continue

# DEPOIS:
if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
    continue
if '/bin/opencode' in line or 'opencode run' in line:
    continue
```

## O que isso remove

1. ✅ Linhas com `/bin/opencode`
2. ✅ Linhas com `opencode run`
3. ✅ Prompts de comando (`$`, `>`, `alyssonpi@`)
4. ✅ Sentinelas (`__JOBDONE_`)

## Teste em andamento

```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Qual a cor do céu?", "agent": "opencode"}'
```

## Esperado

```yaml
summary: "Azul"  # ✅ Apenas a resposta!
```

## Não mais

```yaml
summary: "/home/alyssonpi/.opencode/bin/opencode run Qual a cor do céu? ; echo..."  # ❌
```

## Status

✅ **Filtro melhorado**
✅ **Servidor reiniciado**
⏳ **Teste em andamento**
