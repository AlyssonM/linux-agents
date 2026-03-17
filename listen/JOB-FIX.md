# Fix: Job YAML não atualizou

## Problema identificado

O job `c41038e2` terminou com sucesso (output: "OK"), mas o YAML permaneceu com `status: running`.

### Causa provável
O job foi movido para `jobs/archived/` durante a execução, quando você executou:
```bash
curl -X POST http://127.0.0.1:7600/jobs/clear
```

O worker tentou atualizar `jobs/c41038e2.yaml`, mas o arquivo não existia mais!

## Solução aplicada

YAML foi atualizado manualmente:

```yaml
id: c41038e2
status: completed  ✅ atualizado
prompt: Say OK
agent: opencode
exit_code: 0  ✅ adicionado
summary: OK  ✅ adicionado
duration_seconds: 2  ✅ adicionado
completed_at: '2026-03-17T05:29:40Z'  ✅ adicionado
```

## Prevenção futura

### Verificar antes de limpar

```bash
# 1. Ver se há jobs rodando
grep -l "status: running" ~/Github/linux-agents/listen/jobs/*.yaml

# 2. Ver sessões tmux ativas
tmux ls | grep job-

# 3. Ver via API
curl http://localhost:7600/jobs | jq '.jobs[] | select(.status == "running")'
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

## Melhoria sugerida: /jobs/clear-safe

Adicionar endpoint que pula jobs rodando:

```python
@app.post("/jobs/clear-safe")
def clear_jobs_safe():
    """Limpar apenas jobs completados/failed"""
    count = 0
    skipped = 0
    for f in JOBS_DIR.glob("*.yaml"):
        data = _read_job(f)
        if data.get("status") in ["completed", "failed", "stopped"]:
            shutil.move(str(f), str(ARCHIVED_DIR / f.name))
            count += 1
        else:
            skipped += 1
    return {"archived": count, "skipped": skipped}
```

## Status atual

| Item | Status |
|------|--------|
| **Job c41038e2** | ✅ Atualizado manualmente |
| **YAML** | ✅ Salvo com status correto |
| **Documento** | ✅ JOB-UPDATE-ISSUE.md criado |
| **Git** | ✅ Commitado |

## Documentação

Veja `JOB-UPDATE-ISSUE.md` para:
- Soluções alternativas
- Comandos de verificação
- Melhorias de código sugeridas
