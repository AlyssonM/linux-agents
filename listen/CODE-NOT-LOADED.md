# ❌ PROBLEMA: Novo código não foi carregado!

## Evidência

Debug log mostra:
```
[e2af7505] agent=opencode, prompt=ping, model=
```

Mas DEVERIA mostrar (com o novo código):
```
[<id>] agent=<agent>, session=job-<id>
[<id>] runner=_run_opencode
```

## O que isso significa

O **novo código não foi carregado**! O servidor está rodando com o worker.py antigo.

## Por que?

Reiniciei o servidor mas matou o processo com SIGTERM antes de terminar.

## Solução

1. ✅ Matar todos os processos antigos
2. ✅ Verificar que estão mortos
3. ✅ Iniciar com o novo código
4. ✅ Testar novamente

## Comandos

```bash
# Matar tudo
pkill -9 -f "python.*listen/main.py"
pkill -9 -f "python.*worker.py"

# Verificar
ps aux | grep "[p]ython.*listen"

# Iniciar novo
~/Github/linux-agents/.venv/bin/python listen/main.py > /tmp/listen.log 2>&1 &
```

## Status

❌ **Novo código não carregado**
⏳ **Precisa reiniciar servidor corretamente**
