# ❌ BUG CONFIRMADO: Worker ignora agent "opencode"

## Evidência

### Job 77c22b86
```yaml
id: 77c22b86
prompt: echo ping
updates:
  - Spawned Codex worker in tmux session  # ❌ ERRADO!
```

### Debug log
```
[e2af7505] agent=opencode, prompt=ping, model=
```

✅ **Agent é passado corretamente**
❌ **Mas worker usa "codex"!**

## Problema

O worker NÃO está escrevendo a segunda linha de debug:

```python
# Esta linha aparece:
f.write(f"[{job_id}] agent={agent}, prompt={prompt}, model={model}\n")

# Esta linha NÃO aparece:
f.write(f"[{job_id}] runner={runner.__name__}, agent={agent}\n")
```

Isso significa que o worker está **falhando antes de selecionar o runner**!

## Possível causa

Há uma exceção sendo lançada entre as duas linhas de debug.

## Verificar código

```python
# Get agent runner
runner = AGENT_RUNNERS.get(agent)  # ← Pode retornar None?
if not runner:
    raise SystemExit(f"Unknown agent: {agent}...")
```

Se `AGENT_RUNNERS.get("opencode")` retornar `None`, ele levanta `SystemExit` e o worker morre!

## Verificar AGENT_RUNNERS

```python
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,  # Existe?
}
```

## Possível solução

O código editado pode ter removido "opencode" do AGENT_RUNNERS por engano.

## Ação necessária

1. ✅ Verificar AGENT_RUNNERS no worker.py atual
2. ⏳ Ver se "_run_opencode" existe
3. ⏳ Adicionar debug antes do AGENT_RUNNERS.get()
4. ⏳ Ver se há exceção sendo capturada

## Status

❌ **Bug confirmado**
⏳ **Investigando AGENT_RUNNERS**
