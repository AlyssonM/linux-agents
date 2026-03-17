# OpenCode Directory for linux-agents

**100% compatível com `.claude/` - use com Claude Code ou OpenCode CLI**

## Estrutura

```
.opencode/
├── agents/
│   └── job-system-prompt.md → .claude/agents/
├── commands/
│   ├── prime.md → .claude/commands/
│   ├── rpi-gui-term-user-prompt.md → .claude/commands/
│   ├── install-rpi-sandbox.md → .claude/commands/
│   └── install-engineer-workstation.md → .claude/commands/
├── skills/
│   ├── rpi-gui → .claude/skills/
│   ├── rpi-term → .claude/skills/
│   ├── rpi-job → .claude/skills/
│   └── rpi-client → .claude/skills/
└── STRUCTURE.md
```

## Uso com OpenCode CLI

```bash
# Carregar contexto fundamental
opencode prime

# Executar tarefa de automação
opencode /rpi-gui-term "Listar arquivos em ~/HA/"
```

## Uso com Claude Code

```bash
# Carregar contexto
/prime

# Executar tarefa
/rpi-gui-term "Abrir Chromium e ir para google.com"
```

## Links Simbólicos

Todos os arquivos são **links simbólicos** para `.claude/`:
- Mantém sincronização automática
- Evita duplicação
- Ambos CLIs usam a mesma configuração

## Compatibilidade

| CLI | Diretório | Status |
|-----|-----------|--------|
| **Claude Code** | `.claude/` | ✅ Nativo |
| **OpenCode** | `.opencode/` | ✅ Suportado |
| **Ambos** | Links simbólicos | ✅ Compartilhado |

## Manutenção

- Edite arquivos em `.claude/` (source)
- `.opencode/` reflete automaticamente via links
- Commits afetam ambos os diretórios

## Documentação Completa

Veja `STRUCTURE.md` para documentação detalhada.
