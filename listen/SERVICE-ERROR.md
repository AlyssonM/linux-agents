# Erro: Syntax error no worker.py

## Problema

Systemd não consegue iniciar o serviço:

```
status=1/FAILURE
```

## Provável causa

Erro de syntax no worker.py após a edição.

## Verificar

```bash
cd ~/Github/linux-agents/listen
python main.py 2>&1 | head -20
```

## Solução

Se houver erro de syntax, precisa reverter ou corrigir o worker.py.

## Status

❌ **Serviço não inicia**
⏳ **Verificando logs**
