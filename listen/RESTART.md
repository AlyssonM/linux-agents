# Reiniciar Serviços listen e openclaw-listen

## Passo 1: Matar tmux server (OPCIONAL - CUIDADO!)

⚠️ **AVISO:** Isso vai matar TODAS as sessões tmux, não apenas as do listen!

```bash
tmux kill-server
```

**Só faça isso se:**
- Houver sessões tmux "zumbis" que não respondem
- O worker ficar travado em tmux
- Você souber o que está fazendo

## Passo 2: Reiniciar serviços systemd

```bash
# Reiniciar listen (porta 7600)
systemctl --user restart linux-agents-listen

# Reiniciar openclaw-listen (porta 7610)
systemctl --user restart openclaw-listen
```

## Passo 3: Verificar status

```bash
# Ver status do listen
systemctl --user status linux-agents-listen

# Ver status do openclaw-listen
systemctl --user status openclaw-listen
```

## Passo 4: Verificar portas

```bash
# Ver se listen está na porta 7600
lsof -i :7600

# Ver se openclaw-listen está na porta 7610
lsof -i :7610

# Ou usar netstat
netstat -tulpn | grep -E "7600|7610"
```

## Passo 5: Testar

```bash
# Testar listen (opencode agent)
curl -X POST http://localhost:7600/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say OK", "agent": "opencode"}'

# Testar openclaw-listen
curl -X POST http://localhost:7610/job \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say OK"}'
```

## Troubleshooting

### Serviço não inicia

```bash
# Ver log do systemd
journalctl --user -u linux-agents-listen -n 50
journalctl --user -u openclaw-listen -n 50

# Ver log manual
tail -f /tmp/listen-*.log
```

### Porta já em uso

```bash
# Matar processo na porta 7600
lsof -ti :7600 | xargs kill -9

# Matar processo na porta 7610
lsof -ti :7610 | xargs kill -9
```

### Jobs travados

```bash
# Limpar jobs (arquivar)
curl -X POST http://localhost:7600/jobs/clear
curl -X POST http://localhost:7610/jobs/clear
```

## Arquitetura

| Serviço | Porta | Agents | PID File | Log |
|---------|-------|--------|----------|-----|
| **listen** | 7600 | codex, opencode | - | /tmp/listen-*.log |
| **openclaw-listen** | 7610 | openclaw | - | /tmp/openclaw-listen-*.log |

## Resumo Rápido

```bash
# Reiniciar tudo
systemctl --user restart linux-agents-listen openclaw-listen

# Verificar status
systemctl --user status linux-agents-listen openclaw-listen

# Ver portas
lsof -i :7600 -i :7610
```
