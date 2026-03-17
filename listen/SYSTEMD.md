# Problema: systemctl --user com sudo

## Erro

```
sudo systemctl --user restart linux-agents-listen
Failed to connect to user scope bus via $DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined
```

## Causa

O `sudo` muda para o usuário root, mas `--user` tenta conectar ao bus do usuário original. Isso gera conflito.

## Soluções

### Opção 1: Usar sem sudo (RECOMENDADO)

```bash
# ❌ ERRADO
sudo systemctl --user restart linux-agents-listen

# ✅ CORRETO
systemctl --user restart linux-agents-listen
```

### Opção 2: Usar sudo com --machine

```bash
# Substitua 'alyssonpi' pelo seu usuário
sudo systemctl --user --machine=alyssonpi@.host restart linux-agents-listen
```

### Opção 3: Usar loginctl

```bash
# Obter sessão do usuário
loginctl list-sessions

# Reiniciar serviço na sessão
sudo systemctl restart user@$(id -u).service
```

## Verificar se os serviços existem

```bash
# Listar serviços do usuário
systemctl --user list-units | grep -E "(linux-agents|openclaw|listen)"

# Ver arquivos de serviço
ls ~/.config/systemd/user/*.service
```

## Criar serviços systemd (se não existirem)

Se os serviços não existirem, crie os arquivos:

### linux-agents-listen.service

```bash
cat > ~/.config/systemd/user/linux-agents-listen.service << 'EOF'
[Unit]
Description=Linux Agents Listen Server (port 7600)
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/Github/linux-agents
ExecStart=%h/.local/share/virtualenvs/linux-agents-*/bin/python listen/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
```

### openclaw-listen.service

```bash
cat > ~/.config/systemd/user/openclaw-listen.service << 'EOF'
[Unit]
Description=OpenClaw Listen Server (port 7610)
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/Github/linux-agents/openclaw-listen
ExecStart=%h/.local/share/virtualenvs/linux-agents-*/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
```

## Habilitar e iniciar

```bash
# Recarregar systemd
systemctl --user daemon-reload

# Habilitar auto-start no login
systemctl --user enable linux-agents-listen
systemctl --user enable openclaw-listen

# Iniciar agora
systemctl --user start linux-agents-listen
systemctl --user start openclaw-listen

# Verificar status
systemctl --user status linux-agents-listen
systemctl --user status openclaw-listen
```

## Iniciar manualmente (sem systemd)

Se systemd não funcionar, inicie manualmente:

```bash
# listen (porta 7600)
cd ~/Github/linux-agents
.venv/bin/python listen/main.py > /tmp/listen.log 2>&1 &

# openclaw-listen (porta 7610)
cd ~/Github/linux-agents/openclaw-listen
python main.py > /tmp/openclaw-listen.log 2>&1 &
```

## Verificar portas

```bash
# Verificar se os serviços estão rodando
lsof -i :7600  # listen
lsof -i :7610  # openclaw-listen

# Ou usar netstat
netstat -tulpn | grep -E "7600|7610"
```

## Resumo

✅ **Use SEMPRE sem sudo:**
```bash
systemctl --user restart linux-agents-listen
```

❌ **NUNCA use sudo com --user:**
```bash
sudo systemctl --user restart ...  # ERRADO!
```
