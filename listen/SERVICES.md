# Criar e Habilitar Serviços systemd

## Serviços criados em:
```bash
~/.config/systemd/user/linux-agents-listen.service    # Porta 7600
~/.config/systemd/user/openclaw-listen.service        # Porta 7610
```

## Passo 1: Recarregar systemd
```bash
systemctl --user daemon-reload
```

## Passo 2: Habilitar auto-start no login
```bash
systemctl --user enable linux-agents-listen
systemctl --user enable openclaw-listen
```

## Passo 3: Iniciar os serviços
```bash
# Iniciar listen (porta 7600)
systemctl --user start linux-agents-listen

# Iniciar openclaw-listen (porta 7610)
systemctl --user start openclaw-listen
```

## Passo 4: Verificar status
```bash
# Ver status do listen
systemctl --user status linux-agents-listen

# Ver status do openclaw-listen
systemctl --user status openclaw-listen

# Ver se as portas estão abertas
lsof -i :7600
lsof -i :7610
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

## Comandos úteis
```bash
# Reiniciar serviços
systemctl --user restart linux-agents-listen
systemctl --user restart openclaw-listen

# Parar serviços
systemctl --user stop linux-agents-listen
systemctl --user stop openclaw-listen

# Desabilitar auto-start
systemctl --user disable linux-agents-listen
systemctl --user disable openclaw-listen

# Ver logs
journalctl --user -u linux-agents-listen -f
journalctl --user -u openclaw-listen -f
```

## Logs dos servidores
```bash
# listen
tail -f /tmp/listen-server.log

# openclaw-listen
tail -f /tmp/openclaw-listen-server.log
```

## Alternativa manual (se systemd não funcionar)
```bash
# listen
cd ~/Github/linux-agents
.venv/bin/python listen/main.py > /tmp/listen-manual.log 2>&1 &

# openclaw-listen
cd ~/Github/linux-agents/openclaw-listen
python main.py > /tmp/openclaw-listen-manual.log 2>&1 &
```
