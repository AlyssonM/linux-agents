# 🔍 ENCONTREI O PROBLEMA!

## Job 851ceb52 (mais recente)

```yaml
# Não tem agent no YAML!
id: 851ceb52
status: failed
prompt: ping
# ❌ SEM "agent:"
```

## Isso explica tudo!

O YAML NÃO tem o campo `agent:` quando é criado!

## Causa

O main.py cria o YAML assim:

```python
data = {
    "id": job_id,
    "status": "running",
    "prompt": req.prompt,
    "agent": req.agent,  # ← Adiciona aqui
    ...
}
_write_job(job_file, data)
```

Mas o YAML não está sendo escrito com o campo `agent:`!

## Possível causa

A função `_write_job()` ou `_write_yaml()` pode estar removendo campos vazios ou None.

## Verificar

```python
def _write_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

Se `req.agent` for None ou vazio, o YAML pode não incluir o campo.

## Solução

Garantir que o agent sempre tenha um valor:

```python
data = {
    ...
    "agent": req.agent or "codex",  # ← Default se None
    ...
}
```

## Testar

```bash
# Ver YAML completo
cat ~/Github/linux-agents/listen/jobs/851ceb52.yaml

# Ver se tem agent:
grep "^agent:" ~/Github/linux-agents/listen/jobs/851ceb52.yaml
```

## Status

✅ **Problema identificado**
⏳ **YAML não tem campo agent**
⏳ **Precisa garantir que agent sempre seja escrito**
