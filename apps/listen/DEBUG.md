# 📋 Multi-Agent Support - Debug Notes

## Agents Disponíveis

### ✅ **opencode** (Recomendado)
- **Status:** Disponível e funcional
- **Binário:** `~/.opencode/bin/opencode`
- **Model support:** ❌ Não implementado ainda
- **Testado:** ✅ Job 772c8552 completou com sucesso
- **Uso:**
```bash
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "minha tarefa", "agent": "opencode"}'
```

### ⚠️ **codex** (Limitado)
- **Status:** OpenAI API em reset (até 18/03/2026)
- **Model support:** ✅ Sim
- **Notação:** Aguarde reset do limite para usar

### ❓ **claude** (Alias)
- **Status:** Alias para `opencode`
- **Comportamento:** Usa opencode por baixo
- **Uso:** Mesmo que opencode

### ❌ **openclaw** (Removido)
- **Motivo:** Já existe `openclaw-listen` dedicado
- **Use em vez:** `~/Github/linux-agents/openclaw-listen/`
- **Porta:** 7610

## Problema: Syntax Error (RESOLVIDO)

### Erro
```python
File "worker.py", line 236
    se ""
       ^^
SyntaxError: invalid syntax
```

### Causa
Digitação erro na última linha do arquivo: `se ""` em vez de `main(...)`

### Solução
```bash
# Corrigido em commit 2741522
git show 2741522
```

## Testes Realizados

| Agent | Job ID | Status | Nota |
|-------|--------|--------|------|
| opencode | 772c8552 | ✅ completed | SUCCESS! |
| opencode | 4816404e | ❌ syntax error | Corrigido |
| opencode | 1b206e91 | ⏳ hung | Zombie process |

## Problema: Servidor não inicia (RESOLVIDO)

### Sintoma
```
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 7600): address already in use
```

### Solução
```bash
# Matar processos antigos
ps aux | grep "[p]ython.*listen/main.py" | awk '{print $2}' | xargs -r kill

# Reiniciar tmux server (se necessário)
tmux kill-server  # CUIDADO: mata todas as sessões tmux

# Reiniciar servidor
cd ~/Github/linux-agents
.venv/bin/python listen/main.py > /tmp/listen.log 2>&1 &
```

## Systemd Service

Para reiniciar o serviço systemd:

```bash
# Reiniciar listen (porta 7600)
systemctl --user restart linux-agents-listen

# Reiniciar openclaw-listen (porta 7610)
systemctl --user restart openclaw-listen

# Ver status
systemctl --user status linux-agents-listen
systemctl --user status openclaw-listen
```

## Serviços Ativos

| Serviço | Porta | PID | Status |
|---------|-------|-----|--------|
| listen | 7600 | - | Systemd ou manual |
| openclaw-listen | 7610 | 42304 | ✅ Running |

## Comandos Úteis

### Verificar jobs
```bash
# Listar todos os jobs
curl http://localhost:7600/jobs

# Ver job específico
curl http://localhost:7600/job/772c8552

# Limpar jobs (arquivar)
curl -X POST http://localhost:7600/jobs/clear
```

### Debug tmux
```bash
# Listar sessões tmux
tmux ls

# Ver output de sessão específica
tmux capture-pane -p -t job-JOBID -S -500

# Matar sessão específica
tmux kill-session -t job-JOBID
```

### Ver logs
```bash
# Log do servidor
tail -f /tmp/listen-*.log

# Log do worker específico
cat ~/Github/linux-agents/listen/jobs/JOBID.yaml
```

## Recomendações

1. **Use opencode** - Funciona perfeitamente
2. **Reinicie tmux server** se tiver problemas com sessões
3. **Reinicie systemd** se o serviço não responder
4. **Verifique logs** em `/tmp/listen-*.log`

## Próximos Passos

1. ✅ Remover openclaw do listen
2. ✅ Documentar openclaw-listen separadamente
3. ⏳ Adicionar model support ao opencode
4. ⏳ Testar codex após reset da API (18/03)
