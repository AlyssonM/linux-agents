# Resumo: Systemd rodando, mas YAML não é criado no disco

## Status

### ✅ Systemd funcionando

```
Active: active (running)
Main PID: 174637
http://0.0.0.0:7600
```

### ❌ YAML não existe no disco

```bash
ls ~/Github/linux-agents/listen/jobs/49ec0b83.yaml
# No such file or directory
```

### ✅ Mas a API retorna o YAML

```bash
curl http://localhost:7600/job/49ec0b83
# Retorna dados do job
```

## Problema identificado

1. **Job foi criado** (API retorna dados)
2. **Arquivo não está em `jobs/`**
3. **Job mostra "Codex worker"** em vez de "opencode"
4. **Status: failed** (exit_code 1)

## O que está acontecendo

O YAML pode estar:
1. Em `jobs/archived/` (limpeza automática?)
2. Sendo deletado após completion
3. O worker não está salvando o agent corretamente

## Verificar

```bash
# Procurar em todos os lugares
find ~/Github/linux-agents/listen/jobs* -name "49ec0b83.yaml"

# Ver archived
ls ~/Github/linux-agents/listen/jobs/archived/ | grep 49ec0b83
```

## Causa provável do "Codex worker"

O agent não está sendo lido corretamente pelo worker:

```python
# worker.py
agent = sys.argv[3]  # Deveria ser "opencode"
# Mas AGENT_RUNNERS pode estar usando default "codex"
```

## Debug necessário

1. ✅ Systemd está rodando
2. ❌ YAML não está no disco
3. ⏳ Verificar onde o arquivo foi
4. ⏳ Debugar por que mostra "Codex worker"

## Próximos passos

1. Encontrar onde o YAML está
2. Verificar se o agent está salvo corretamente
3. Debugar o worker para ver qual agent está recebendo
