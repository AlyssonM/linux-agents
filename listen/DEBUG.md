# 📋 Multi-Agent Support - Status Atual

## Agents Disponíveis

### ✅ **opencode** (Recomendado)
- **Status:** Disponível e funcional
- **Binário:** `~/.opencode/bin/opencode`
- **Model support:** ❌ Não implementado ainda
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

### ❓ **openclaw** (Experimental)
- **Status:** Não disponível para testes
- **Requer:** Gateway OpenClaw rodando
- **Model support:** ✅ Sim

## Problema Atual

O job `1b206e91` com opencode está rodando mas:
- `session: ''` está vazio (tmux session não criada)
- `updates: []` vazio
- `status: running` por muito tempo

**Investigação necessária:**
- Verificar se `_run_opencode()` está criando sessão tmux corretamente
- Verificar se opencode binary está funcionando

## Testes Realizados

| Agent | Job ID | Status | Nota |
|-------|--------|--------|------|
| openclaw | c2b7d463 | ❌ failed | tmux capture-pane error |
| opencode | 1b206e91 | ⏳ running | session empty, hanging |

## Próximos Passos

1. Debug `_run_opencode()` - adicionar logs
2. Verificar se opencode precisa de argumentos diferentes
3. Testar opencode manualmente fora do tmux
