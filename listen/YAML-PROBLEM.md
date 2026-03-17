# Problema: Job não gera YAML correto

## Situação

### ✅ Systemd está rodando

```
Active: active (running)
Main PID: 174637
```

### ❌ YAML existe mas com problema

```bash
curl http://localhost:7600/job/49ec0b83
```

Retorna:
```yaml
id: 49ec0b83
status: failed
prompt: ping
updates:
  - Spawned Codex worker in tmux session  # ❌ ERRADO!
exit_code: 1
```

## Problema identificado

O YAML **foi criado**, mas:
1. **Não mostra o agent** (deveria ter `agent: opencode`)
2. **Mostra "Codex worker"** em vez de "OpenCode CLI worker"
3. **Status: failed** com exit_code 1

## Causa provável

O agent não está sendo salvo no YAML inicial, ou o worker está usando codex por padrão.

## Verificação

Verificar se o agent está no request:

```python
# No main.py
class JobRequest(BaseModel):
    prompt: str
    agent: str = "codex"  # ✅ Tem default
    model: str | None = None
```

```python
# Criar job
data = {
    "id": job_id,
    "agent": req.agent,  # ✅ Passado
    ...
}
```

```python
# Worker
proc = subprocess.Popen(
    [sys.executable, str(worker_path), job_id, req.prompt, req.agent, req.model or ""],
    ...
)
```

## Possível problema

O worker pode não estar lendo o agent corretamente do argv.

## Debug

```bash
# Ver YAML completo
cat ~/Github/linux-agents/listen/jobs/49ec0b83.yaml

# Ver se agent está lá
grep "agent:" ~/Github/linux-agents/listen/jobs/49ec0b83.yaml
```

## Solução

Se o agent não está no YAML, precisamos garantir que:
1. O agent é passado no spawn do worker
2. O worker lê o agent do argv[3]
3. O AGENT_RUNNERS tem o agent correto

## Status

⏳ **Investigando**
- Systemd: ✅ Rodando
- YAML criado: ✅ Sim
- Agent no YAML: ❌ Não aparece
- Worker usando codex: ❌ Incorreto
