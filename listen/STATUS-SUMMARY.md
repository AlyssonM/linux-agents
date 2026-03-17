# 📋 Status: Systemd OK, YAML bugado

## Resumo

- ✅ **Systemd está rodando** (PID 174637)
- ❌ **YAML não aparece no disco**
- ❌ **Worker usa "codex" em vez de "opencode"**

## Systemd: ✅ FUNCIONANDO

```
Active: active (running)
Main PID: 174637
Port: 7600
```

## Problema 1: YAML não está no disco

```bash
ls ~/Github/linux-agents/listen/jobs/49ec0b83.yaml
# No such file or directory ❌
```

Mas a API retorna dados (o job existe em algum lugar).

## Problema 2: Agent errado

Job mostra:
```yaml
updates:
  - Spawned Codex worker in tmux session  # ❌ ERRADO!
```

Deveria ser:
```yaml
updates:
  - Spawned OpenCode CLI worker with default model  # ✅ CORRETO!
```

## Isso indica

O **worker está recebendo o agent errado** ou **AGENT_RUNNERS está mapeando errado**.

## Próximos passos

1. Verificar se main.py está passando agent corretamente
2. Verificar se worker.py está lendo argv[3]
3. Adicionar debug prints no worker
4. Verificar AGENT_RUNNERS mapeamento

## Resumo para o usuário

**Sim, systemd está rodando** ✅

**Mas há dois problemas:**
1. YAML não aparece no disco (pode estar em archived)
2. Worker está usando "codex" em vez de "opencode" (bug)

**Precisa debugar o worker.**
