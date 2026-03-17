# Limpeza de Jobs - listen/

## Data: 2026-03-17 02:27

### Antes da limpeza
```bash
# Jobs em listen/jobs/
ls jobs/*.yaml | wc -l
# [contagem de jobs]
```

### Ação executada
```bash
# Arquivar todos os jobs
curl -X POST http://127.0.0.1:7600/jobs/clear

# Resultado: {"archived": <count>}
```

### Depois da limpeza
```bash
# Jobs arquivados
ls jobs/archived/*.yaml | wc -l

# Diretório de jobs ativos
ls jobs/*.yaml
# (deve estar vazio ou apenas com jobs recentes)
```

## Como limpar jobs manualmente

### Opção 1: API (RECOMENDADO)
```bash
# Arquivar todos os jobs
curl -X POST http://localhost:7600/jobs/clear

# Ver quantos foram arquivados
curl http://localhost:7600/jobs
```

### Opção 2: Manualmente
```bash
cd ~/Github/linux-agents/listen

# Mover todos para archived
mv jobs/*.yaml jobs/archived/

# Ou apenas os antigos (> 1 dia)
find jobs/*.yaml -mtime +1 -exec mv {} jobs/archived/ \;
```

### Opção 3: Deletar permanentemente
```bash
# CUIDADO: Não recupera depois!
cd ~/Github/linux-agents/listen
rm jobs/*.yaml
```

## Limpeza agendada (cron)

```bash
# Adicionar ao crontab
crontab -e

# Limpar jobs todos os dias às 3 da manhã
0 3 * * * curl -X POST http://localhost:7600/jobs/clear
```

## Ver jobs arquivados
```bash
# Listar
ls ~/Github/linux-agents/listen/jobs/archived/

# Ver conteúdo específico
cat ~/Github/linux-agents/listen/jobs/archived/JOBID.yaml

# Contar
ls ~/Github/linux-agents/listen/jobs/archived/*.yaml | wc -l
```

## Restaurar job (se necessário)
```bash
cd ~/Github/linux-agents/listen
mv jobs/archived/JOBID.yaml jobs/
```

## Limpeza de arquivados antigos
```bash
# Deletar arquivados com mais de 7 dias
cd ~/Github/linux-agents/listen
find jobs/archived/*.yaml -mtime +7 -delete
```

## Resumo da limpeza

| Ação | Comando |
|------|---------|
| **Arquivar todos** | `curl -X POST http://localhost:7600/jobs/clear` |
| **Ver jobs ativos** | `curl http://localhost:7600/jobs` |
| **Ver arquivados** | `ls jobs/archived/` |
| **Limpar arquivados antigos** | `find jobs/archived/*.yaml -mtime +7 -delete` |
