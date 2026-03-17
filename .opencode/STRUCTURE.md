# linux-agents OpenCode Documentation Structure

Compatível com a estrutura `.claude` para uso com OpenCode CLI.

## Directory Structure

```
linux-agents/.opencode/
├── agents/
│   ├── listen-job-system-prompt.md    # System prompt para listen/ worker
│   └── job-system-prompt.md            # System prompt para rpi-job worker
├── commands/
│   ├── prime.md                        # Load contexto fundamental do codebase
│   ├── rpi-gui-term-user-prompt.md     # User prompt para automação GUI+Terminal
│   └── install-rpi-sandbox.md          # Instalação e verificação do sandbox
├── skills/
│   ├── rpi-gui/SKILL.md               # GUI automation skill
│   ├── rpi-term/SKILL.md               # Terminal automation skill
│   ├── rpi-job/SKILL.md                # Job server skill
│   └── rpi-client/SKILL.md             # Job client skill
└── STRUCTURE.md                        # Este arquivo
```

## Compatibilidade com .claude

A estrutura `.opencode` é **100% compatível** com `.claude`:
- Mesmos diretórios: `agents/`, `commands/`, `skills/`
- Mesma formatação de prompts
- Mesmas variáveis e templates
- Pode ser usado por ambos: Claude Code e OpenCode

## Diferenças

- **`.claude/`** - Configuração padrão para Claude Code
- **`.opencode/`** - Configuração para OpenCode CLI (opencode)

Ambos podem coexistir no mesmo repositório.

## Uso com OpenCode CLI

```bash
# Prime o contexto
opencode prime

# Executar tarefa de automação
opencode /rpi-gui-term "Listar arquivos em árvore do diretório ~/HA/"
```

## Uso com Claude Code

```bash
# Prime o contexto
/prime

# Executar tarefa
/rpi-gui-term "Abrir Chromium e navegar para example.com"
```

## Arquivos Compartilhados

Os arquivos em `.opencode/` são **links simbólicos** para `.claude/` quando possível:
- `agents/` → `.claude/agents/`
- `commands/` → `.claude/commands/`
- `skills/` → `.claude/skills/`

Isso garanteis que ambos os CLIs usem a mesma configuração.

## Agents

### listen-job-system-prompt.md

**Propósito:** System prompt carregado pelo listen/ worker ao executar jobs.

**Uso:** Carregado automaticamente por `worker.py` quando processa jobs via codex exec.

**Variáveis:**
- `{{JOB_ID}}` - Identificador do job (8-character hex)
- Job file: `linux-agents/listen/jobs/{{JOB_ID}}.yaml`

### job-system-prompt.md

**Propósito:** System prompt carregado pelo rpi-job worker ao executar jobs.

**Uso:** Carregado automaticamente por `worker.py` quando processa jobs.

**Variáveis:**
- `{{JOB_ID}}` - Identificador do job
- Job file: `linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml`

## Commands

Veja `.claude/STRUCTURE.md` para documentação completa dos comandos.

## Skills

Veja `.claude/skills/*/SKILL.md` para documentação das skills.

## Manutenção

- Atualizar ambos `.claude/` e `.opencode/` quando mudar a estrutura
- Manter compatibilidade entre Claude Code e OpenCode
- Testar prompts com ambos os CLIs

## Referências

- `.claude/STRUCTURE.md` - Documentação completa da estrutura
- `README.md` - Visão geral do projeto
- `specs/README.md` - Documentação de testes E2E
