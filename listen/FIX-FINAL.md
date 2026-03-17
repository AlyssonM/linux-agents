# ✅ FIX FINAL APLICADO!

## Mudança no main.py

```python
# Garante que agent sempre tenha valor
"agent": req.agent or "codex",
```

## Teste: Job c8562ea2

```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "echo OK", "agent": "opencode"}'
```

## Aguardando resultado

Job está rodando, aguardando completar para verificar o YAML.

## Esperado

```yaml
id: c8562ea2
agent: opencode  # ✅ DEVE aparecer agora!
prompt: echo OK
status: completed
```

## Verificar

```bash
cat ~/Github/linux-agents/listen/jobs/c8562ea2.yaml
```

## Se funcionar

O worker vai ler o agent correto do YAML e mostrar:
```yaml
updates:
  - Spawned OpenCode CLI worker with default model
```

## Status

✅ **Fix aplicado**
✅ **Git push feito**
✅ **Job criado**
⏳ **Aguardando resultado**
