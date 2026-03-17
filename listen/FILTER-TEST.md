# ✅ FIX APLICADO: Filtro melhorado para remover comandos

## Mudança no código

```python
# Removido '/' da lista de prefixes (era muito agressivo)
# Adicionado filtro específico para comandos opencode

if any(line.strip().startswith(prefix) for prefix in ['$', '>', 'alyssonpi@']):
    continue
# Skip lines with binary paths or opencode command
if '/bin/opencode' in line or 'opencode run' in line:
    continue
```

## O que isso remove

1. ✅ Linhas com `/bin/opencode`
2. ✅ Linhas com `opencode run`
3. ✅ Prompts de comando (`$`, `>`, `alyssonpi@`)
4. ✅ Sentinelas (`__JOBDONE_`)
5. ✅ Linhas vazias

## Teste: Job d10cfcfc

```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Qual a cor do céu?", "agent": "opencode"}'
```

## Aguardando resultado

Job está rodando, aguardando ver o summary.

## Esperado

```yaml
summary: "Azul"  # ✅ Apenas a resposta!
```

## NÃO mais

```yaml
summary: "/home/alyssonpi/.opencode/bin/opencode run Qual a cor do céu?..."  # ❌
```

## Commit

```
d188bbe fix: improve tmux output filter to remove command lines
```

## Status

✅ **Código alterado**
✅ **Commit feito**
✅ **Servidor reiniciado**
⏳ **Aguardando resultado do teste**
