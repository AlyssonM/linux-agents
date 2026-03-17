# Problema: Job YAML não atualizou

## Causa provável

O job foi movido para `jobs/archived/` durante a execução, então o worker não conseguiu atualizar o arquivo original.

## Como aconteceu

1. **Job criado**: `jobs/c41038e2.yaml`
2. **Jobs limpos**: Movido para `jobs/archived/c41038e2.yaml`
3. **Worker ainda rodando**: Tentou atualizar `jobs/c41038e2.yaml` (não existe mais!)
4. **Resultado**: YAML não atualizado com status final

## Solução 1: Atualizar manualmente o YAML

```bash
cd ~/Github/linux-agents/listen

# Se está em archived
cat jobs/archived/c41038e2.yaml

# Editar manualmente para adicionar:
# - status: completed
# - exit_code: 0
# - completed_at: timestamp
# - summary: OK
```

## Solução 2: Mover de volta e atualizar

```bash
cd ~/Github/linux-agents/listen

# Mover de volta para jobs/
mv jobs/archived/c41038e2.yaml jobs/

# Verificar conteúdo
cat jobs/c41038e2.yaml
```

## Solução 3: Criar novo job atualizado

```bash
cd ~/Github/linux-agents/listen

# Criar YAML atualizado manualmente
cat > jobs/c41038e2.yaml << 'EOF'
id: c41038e2
status: completed
prompt: Say OK
agent: opencode
model: null
created_at: '2026-03-17T05:27:35Z'
pid: <PID_DO_PROCESSO>
session: job-c41038e2
updates:
  - Spawned OpenCode CLI worker with default model
summary: OK
exit_code: 0
duration_seconds: <DURAÇÃO>
completed_at: '2026-03-17T05:29:XXZ'
EOF
```

## Prevenção: Não limpar jobs durante execução

### Verificar jobs rodando antes de limpar

```bash
# Ver jobs ativos
curl http://localhost:7600/jobs | jq '.jobs[] | select(.status == "running")'

# Ou filtrar no YAML
cd ~/Github/linux-agents/listen
grep -l "status: running" jobs/*.yaml

# Ou verificar tmux
tmux ls | grep job-
```

### Limpar apenas jobs completados

```bash
cd ~/Github/linux-agents/listen

# Mover apenas completed/failed
for f in jobs/*.yaml; do
  if grep -q "status: \(completed\|failed\)" "$f"; then
    mv "$f" jobs/archived/
  fi
done
```

## Solução: Atualizar endpoint /jobs/clear

O endpoint atual move TODOS os jobs, mesmo os rodando.

### Opção 1: Melhorar /jobs/clear

Edite `main.py`:

```python
@app.post("/jobs/clear")
def clear_jobs():
    count = 0
    for f in JOBS_DIR.glob("*.yaml"):
        data = _read_job(f)
        # Mover apenas se não estiver rodando
        if data.get("status") != "running":
            shutil.move(str(f), str(ARCHIVED_DIR / f.name))
            count += 1
    return {"archived": count, "skipped_running": "..."}
```

### Opção 2: Endpoint /jobs/clear-safe

```python
@app.post("/jobs/clear-safe")
def clear_jobs_safe():
    """Limpar apenas jobs completados/failed"""
    count = 0
    skipped = 0
    for f in JOBS_DIR.glob("*.yaml"):
        data = _read_job(f)
        if data.get("status") in ["completed", "failed"]:
            shutil.move(str(f), str(ARCHIVED_DIR / f.name))
            count += 1
        else:
            skipped += 1
    return {"archived": count, "skipped": skipped}
```

## Verificação atual

```bash
# Encontrar onde está o YAML
find ~/Github/linux-agents/listen/jobs* -name "c41038e2.yaml"

# Ver conteúdo
cat $(find ~/Github/linux-agents/listen/jobs* -name "c41038e2.yaml")
```

## Recomendação

Use **`/jobs/clear-safe`** (se implementado) ou verifique manualmente antes de limpar:

```bash
# 1. Ver jobs rodando
grep -l "status: running" ~/Github/linux-agents/listen/jobs/*.yaml

# 2. Se houver, aguarde ou cancele
curl -X DELETE http://localhost:7600/job/<JOB_ID>

# 3. Então limpe
curl -X POST http://localhost:7600/jobs/clear
```
