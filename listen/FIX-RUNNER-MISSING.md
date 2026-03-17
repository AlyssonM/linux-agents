# 🔍 AGENT_RUNNERS está faltando "opencode"!

## Problema encontrado

Lendo o worker.py do commit anterior:

```python
# Around line 152
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,  # claude maps to OpenClaw for now
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,  # ← EXISTE!
}
```

## Mas a edição anterior pode ter removido!

Quando editamos para adicionar o debug logging, podemos ter acidentalmente removido "opencode".

## Verificar

```bash
cd ~/Github/linux-agents/listen
grep -A 5 "AGENT_RUNNERS = {" worker.py
```

## Se estiver faltando

Adicionar de volta:

```python
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_opencode,  # ← claude deve apontar para opencode
    "opencode": _run_opencode,
    # Removido: "openclaw"
}
```

## Ação necessária

1. ✅ Verificar AGENT_RUNNERS no worker.py
2. ⏳ Se faltar "opencode", adicionar
3. ⏳ Commitar fix
4. ⏳ Testar novamente

## Documentação

- **AGENT-BUG.md** - Identificou o problema
- **BUG-CONFIRMED.md** - Evidência coletada
- **FIX-RUNNER-MISSING.md** - Este arquivo

## Status

❌ **AGENT_RUNNERS pode estar faltando "opencode"**
⏳ **Precisa verificar e corrigir**
