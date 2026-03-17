# ✅ DIAGNÓSTICO: Encontrado o problema!

## AGENT_RUNNERS no worker.py

```python
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,  # claude maps to OpenClaw for now
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,  # ✅ EXISTE!
}
```

✅ **"opencode" está no AGENT_RUNNERS!**

## _run_opencode existe?

```bash
grep -n "def _run_opencode" worker.py
```

Se mostrar um número de linha, a função existe.

## Então qual é o problema?

O agent está sendo passado corretamente:
```
[e2af7505] agent=opencode
```

Mas o YAML mostra "Codex worker".

## Possível causa

O debug log só mostra a PRIMEIRA linha, não a SEGUNDA:

```python
# Linha 1: Aparece ✅
f.write(f"[{job_id}] agent={agent}, prompt={prompt}, model={model}\n")

# Linha 2: NÃO aparece ❌
f.write(f"[{job_id}] runner={runner.__name__}, agent={agent}\n")
```

Isso significa que o código está falhando ENTRE as duas linhas!

## O que está entre as linhas?

```python
f.write(f"[{job_id}] agent={agent}, prompt={prompt}, model={model}\n")

# ↓ CÓDIGO ENTRE ↓

runner = AGENT_RUNNERS.get(agent)  # ← Pode falhar aqui?
if not runner:
    raise SystemExit(...)  # ← Ou aqui?

# ↓
data["session"] = session_name  # ← Ou aqui?

# ↓
f.write(f"[{job_id}] runner={runner.__name__}, agent={agent}\n")  # Nunca chega aqui!
```

## Possíveis falhas

1. `AGENT_RUNNERS.get(agent)` retorna `None`
2. `job_file` não existe
3. `_read_yaml(job_file)` falha
4. `data["session"] = ...` falha

## Solução

Mover o debug log para ANTES de qualquer operação que pode falhar.

## Status

✅ **AGENT_RUNNERS tem "opencode"**
❌ **Código falha antes da segunda linha de debug**
⏳ **Precisa mover debug log para capturar o erro**
