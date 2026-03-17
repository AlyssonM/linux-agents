# ❌ BUG ENCONTRADO: main.py não está passando o agent!

## Problema

O main.py está spawnando o worker assim:

```python
proc = subprocess.Popen(
    [sys.executable, str(worker_path), job_id, req.prompt, req.agent, req.model or ""],
    ...
)
```

Isso passa: `[python, worker.py, job_id, prompt, agent, model]`

## Mas o worker espera:

```python
if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("Usage: worker.py <job_id> <prompt> <agent> [model]")
    job_id = sys.argv[1]      # ✅ argv[1]
    prompt = sys.argv[2]      # ✅ argv[2]
    agent = sys.argv[3]       # ✅ argv[3]
    model = sys.argv[4]       # ✅ argv[4]
```

Wait, isso parece correto!

## Mas espera...

O job 77c22b86 é um job ANTIGO! Ele foi criado às '2026-03-17T05:50:08Z'.

O usuário acabou de criar um NOVO job, mas ele está retornando o YAML do job antigo!

## Possível problema

1. O novo job não foi criado (mesmo ID?)
2. O YAML não foi atualizado
3. O API está retornando o job errado

## Verificar

```bash
# Ver jobs recentes
curl http://localhost:7600/jobs | grep '"id":' | head -5

# Ver o YAML no disco
cat ~/Github/linux-agents/listen/jobs/77c22b86.yaml
```

## Se o YAML antigo não tiver agent

O YAML antigo pode não ter o campo `agent:` e o worker está usando o default "codex".

## Debug necessário

Verificar se o NOVO job tem o agent no YAML.
