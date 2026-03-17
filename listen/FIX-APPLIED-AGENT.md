# ✅ FIX APLICADO: Agent sempre tem valor no YAML

## Mudança

```python
# ANTES:
"agent": req.agent,  # ← Pode ser None

# DEPOIS:
"agent": req.agent or "codex",  # ← Sempre tem valor
```

## Isso garante

O campo `agent:` SEMPRE será escrito no YAML, mesmo se `req.agent` for None.

## Teste em andamento

Criando job com `agent: "opencode"` para verificar se o YAML tem o campo.

## Esperado

```yaml
id: <job_id>
agent: opencode  # ✅ DEVE aparecer!
prompt: echo OK
```

## Se funcionar

O worker vai ler `agent: opencode` do YAML e usar o runner correto.

## Status

✅ **Código alterado**
✅ **Servidor reiniciando**
⏳ **Teste em andamento**
