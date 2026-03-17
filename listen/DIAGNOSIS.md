# ✅ Systemd está rodando, mas há problemas

## Status do systemd

```
● linux-agents-listen.service
  Active: active (running) ✅
  Main PID: 174637
  Port: 7600
```

## Problema: YAML não está no disco

```bash
ls ~/Github/linux-agents/listen/jobs/49ec0b83.yaml
# No such file or directory ❌
```

Mas a API retorna:
```bash
curl http://localhost:7600/job/49ec0b83
# Retorna dados do job ✅
```

## Diagnóstico

### 1. Job foi criado com agent errado?

Updates mostra:
```yaml
updates:
  - Spawned Codex worker in tmux session  # ❌ Deveria ser "OpenCode CLI worker"
```

Isso indica que o worker está usando **codex** em vez de **opencode**!

### 2. Possíveis causas

1. **Worker não está recebendo o agent** corretamente
2. **AGENT_RUNNERS não tem "opencode"** mapeado
3. **Worker está usando default "codex"**

### 3. Arquivo pode estar em outro lugar

```bash
# Verificar archived
ls ~/Github/linux-agents/listen/jobs/archived/ | grep 49ec0b83

# Buscar em todo o projeto
find ~/Github/linux-agents/listen -name "49ec0b83.yaml"
```

## Problema no AGENT_RUNNERS?

```python
# worker.py linha ~152
AGENT_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_openclaw,
    "openclaw": _run_openclaw,
    "opencode": _run_opencode,  # ✅ Está lá
}
```

## Possível bug no worker

O worker pode estar lendo `sys.argv` incorretamente:

```python
# worker.py
if len(sys.argv) < 4:
    raise SystemExit("Usage: worker.py <job_id> <prompt> <agent> [model]")
job_id = sys.argv[1]
prompt = sys.argv[2]
agent = sys.argv[3]  # Deveria ser "opencode"
```

## Debug necessário

1. ✅ Verificar AGENT_RUNNERS - OK
2. ⏳ Verificar se agent está sendo passado do main.py
3. ⏳ Verificar se worker está lendo argv[3] corretamente
4. ⏳ Adicionar debug print no worker

## Status atual

| Item | Status |
|------|--------|
| **Systemd** | ✅ Rodando |
| **API** | ✅ Respondendo |
| **YAML no disco** | ❌ Não encontrado |
| **Agent correto** | ❌ Usando "codex" |

## Ação necessária

Debugar por que o worker está usando "codex" quando deveria usar "opencode".
