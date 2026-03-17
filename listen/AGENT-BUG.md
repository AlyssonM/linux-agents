# ❌ Problema encontrado: Worker usando "codex" em vez de "opencode"

## Evidência

Job criado com `agent: opencode`:

```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ping", "agent": "opencode"}'
```

Mas o YAML mostra:
```yaml
updates:
  - Spawned Codex worker in tmux session  # ❌ ERRADO!
```

Deveria mostrar:
```yaml
updates:
  - Spawned OpenCode CLI worker with default model  # ✅ CORRETO!
```

## Diagnóstico

O worker está recebendo ou usando o agent errado.

## Possíveis causas

1. **main.py não está passando agent** para o worker
2. **worker.py não está lendo argv[3]** corretamente
3. **AGENT_RUNNERS está usando default "codex"**

## Código atual do main.py

```python
class JobRequest(BaseModel):
    prompt: str
    agent: str = "codex"  # ✅ Default codex
    model: str | None = None

# Criar job
data = {
    "agent": req.agent,  # ✅ Passa agent
    ...
}

# Spawn worker
proc = subprocess.Popen(
    [sys.executable, str(worker_path), job_id, req.prompt, req.agent, req.model or ""],
    ...
)
```

**O main.py está correto!** ✅

## Código do worker.py

```python
def main(job_id: str, prompt: str, agent: str = "codex", model: str = "") -> None:
    # ...
    runner = AGENT_RUNNERS.get(agent)
```

**O worker tem default "codex"!** ⚠️

## Problema

Se o agent não for passado corretamente, ele usa o default "codex".

## Verificar

1. ✅ main.py passa agent: SIM
2. ⚠️ worker tem default "codex"
3. ⏳ Verificar se argv[3] está sendo lido

## Conclusão

**Sim, systemd está rodando** ✅

**Mas o worker está usando "codex" em vez de "opencode"** ❌

**Precisa debugar por que o agent não está sendo passado corretamente.**
