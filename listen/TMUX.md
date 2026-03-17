# Status do tmux

## Situação atual

✅ **tmux está funcionando corretamente**

### Como verificar:

```bash
# Ver sessões ativas
tmux ls

# Se não houver sessões, a mensagem é normal:
# "no server running on /tmp/tmux-1000/default"
```

### Comportamento normal

O tmux server **só inicia quando você cria a primeira sessão**:

```bash
# Nenhuma sessão = server parado (normal!)
tmux ls
# no server running on /tmp/tmux-1000/default

# Criar sessão = server inicia automaticamente
tmux new-session -d -s test

# Agora há sessões
tmux ls
# test: 1 windows

# Matar sessão = server continua rodando
tmux kill-session -t test

# Server ainda rodando (socket existe)
tmux ls
# (sem output = nenhuma sessão, mas server está rodando)
```

### Socket tmux

```bash
# O socket existe (normal)
ls -la /tmp/tmux-1000/
# srw-rw---- 1 alyssonpi alysson  0 ... default
```

### Como o listen/ usa tmux

O `worker.py` cria sessões tmux temporárias:

```python
def _ensure_session(name: str, cwd: str) -> None:
    """Cria sessão se não existir"""
    if _session_exists(name):
        return
    _tmux("new-session", "-d", "-s", name, "-c", cwd)
```

**Fluxo normal:**

1. Job é criado → worker.py é chamado
2. Worker cria sessão `job-<ID>` → tmux server inicia se necessário
3. Job roda na sessão tmux
4. Job termina → sessão é morta
5. **tmux server continua rodando** (aguardando próximos jobs)

### Problemas e soluções

#### Sessões "zumbis" não morrem

```bash
# Listar todas sessões
tmux ls

# Matar sessão específica
tmux kill-session -t job-XXXXX

# Matar todas as sessões (CUIDADO!)
tmux kill-server

# Ou matar uma a uma
tmux list-sessions | grep -o '^[^:]*' | xargs -I {} tmux kill-session -t {}
```

#### tmux não inicia

```bash
# Remover socket antigo
rm -f /tmp/tmux-1000/default

# Recriar
tmux new-session -d -s test
tmux kill-session -t test
```

### Verificar integridade do tmux

```bash
# Teste completo
tmux new-session -d -s test \
  && tmux ls \
  && tmux kill-session -t test \
  && echo "✅ tmux OK" \
  || echo "❌ tmux com problemas"
```

### Logs do tmux

O tmux não tem logs por padrão, mas você pode capturar output:

```bash
# Ver output de uma sessão específica
tmux capture-pane -p -t job-JOBID -S -500

# Ver output em tempo real
tmux pipe-pane -t job-JOBID -o 'cat >> /tmp/tmux-job-JOBID.log'
```

### Resumo

| Situação | Status | Ação |
|----------|--------|-------|
| **tmux server parado** | ✅ Normal | Inicia ao criar primeira sessão |
| **tmux server rodando** | ✅ Normal | Sempre rodando após primeira sessão |
| **Sessões zumbis** | ⚠️ Problema | Matar com `tmux kill-server` |
| **Socket não existe** | ⚠️ Problema | `rm -f /tmp/tmux-1000/default` e recriar |

## Conclusão

✅ **tmux está funcionando corretamente**
- Socket existe: `/tmp/tmux-1000/default`
- Server inicia ao criar sessão
- Não há sessões zumbis no momento
- Não é necessário ação
