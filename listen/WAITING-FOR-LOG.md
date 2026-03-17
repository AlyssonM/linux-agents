# ⏳ Aguardando job completar para ver debug log

## Status

Job `4374c441` está rodando, aguardando ver o debug log.

## Debug log atual

```
[e2af7505] agent=opencode, prompt=ping, model=
```

## Ainda não mostra o runner

O worker só escreve a segunda linha quando seleciona o runner.

## Próximo passo

Aguardar job completar para ver:
```bash
[4374c441] runner=_run_opencode, agent=opencode
```

Se mostrar `_run_codex`, o bug está no AGENT_RUNNERS.
Se mostrar `_run_opencode`, o bug está no agent display ou em outro lugar.

## Comando para verificar

```bash
sleep 10 && cat /tmp/worker-debug.log
```

## Resumo

✅ **Debug logging adicionado**
✅ **Primeiro job testado (e2af7505)**
⏳ **Aguardando job atual (4374c441) completar**
