# Linux Agents

Projeto de automação para Linux (Raspberry Pi 4) usando OpenClaw AI agent framework.

## Visão Geral

Este projeto contém agentes de automação para Linux, incluindo GUI automation, terminal automation, e job processing.

**Status do projeto:** ✅ **PRODUCTION READY**

## Componentes

### Core Agents

- **`rpi-gui/`** - GUI automation para Linux (X11/Wayland)
  - Screenshot capture (grim/scrot)
  - OCR (tesseract)
  - Mouse/keyboard automation (xdotool)
  - Window management (wmctrl)
  - **Status:** ✅ Production-ready

- **`rpi-job/`** - Simple subprocess job server
  - Shell script jobs
  - YAML job state
  - **Status:** ✅ Stable

- **`listen/`** - External agent CLI runtime
  - `codex exec` + tmux integration
  - **Status:** ✅ Stable

- **`openclaw-listen/`** - OpenClaw-native job server ⭐ **RECOMMENDED**
  - REST API for job submission
  - Subagent execution (isolated subprocess)
  - YAML job state
  - **Status:** ✅ Production-ready
  - **Docs:** [OpenClaw Listen](../obsidian-vault/linux-agents/OpenClaw%20Listen.md)

### Especificações e Testes

- **`specs/`** - Especificações técnicas e testes E2E
  - `gui-workflow.md` - GUI automation tests
  - `terminal-and-browser.md` - Terminal integration tests
  - `openclaw-listen-architecture.md` - Architecture docs

## Quick Start

### 1. Setup Python venv

```bash
cd linux-agents
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Testar GUI automation

```bash
cd rpi-gui
python -m rpi_gui.commands.see
python -m rpi_gui.commands.type --text "Hello, World!"
```

### 3. Iniciar openclaw-listen server

```bash
cd openclaw-listen
python main.py
```

### 4. Criar job via API

```bash
curl -X POST http://localhost:7610/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "List files in current directory",
    "execution": {"strategy": "auto", "timeout_seconds": 30}
  }'
```

## Arquitetura

```
linux-agents/
├── rpi-gui/              # GUI automation commands
│   ├── commands/         # Individual command modules
│   └── modules/          # Shared utilities
│
├── rpi-job/              # Simple job server
│   └── jobs/             # Job state YAML files
│
├── listen/               # External agent runtime
│   └── jobs/             # Job state YAML files
│
├── openclaw-listen/      # OpenClaw-native job server ⭐
│   ├── main.py           # FastAPI REST API
│   ├── worker.py         # Job worker (subagent)
│   └── jobs/             # Job state YAML files
│
├── specs/                # Technical specs and tests
└── README.md             # This file
```

## Serviços Systemd

Todos os componentes têm serviços systemd configurados:

```bash
# openclaw-listen (recommended)
systemctl --user start openclaw-listen
systemctl --user status openclaw-listen

# rpi-job (simple jobs)
systemctl --user start rpi-job

# listen (external agent)
systemctl --user start listen
```

## Comparação de Job Servers

| Componente | Tecnologia | Isolamento | API REST | Recomendado |
|------------|-----------|-------------|----------|-------------|
| **rpi-job** | subprocess shell | Baixo | ❌ | Simples |
| **listen** | `codex exec` + tmux | Médio | ❌ | Integrado |
| **openclaw-listen** | OpenClaw agent CLI | Alto | ✅ | ⭐ **SIM** |

## GUI Automation

Comandos disponíveis em `rpi-gui/`:

```bash
# Capturar tela
python -m rpi_gui.commands.see

# Mouse/keyboard
python -m rpi_gui.commands.click --x 100 --y 200
python -m rpi_gui.commands.type --text "Hello"
python -m rpi_gui.commands.hotkey --key ctrl+c

# Window management
python -m rpi_gui.commands.focus --title "Chromium"
```

## Testes E2E

Rodar suite de testes completa:

```bash
cd specs
./run-e2e-tests.sh
```

Resultados em `artifacts/e2e/YYYYMMDD-HHMM/`

## Deploy

### Requirements

- Python 3.11+
- OpenClaw CLI instalado
- X11/Wayland display server
- Systemd (para serviços)

### Instalação

```bash
# Clonar repositório
git clone https://github.com/AlyssonM/linux-agents.git
cd linux-agents

# Setup venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Instalar dependências de GUI
sudo apt install -y tesseract-ocr xdotool wmctrl scrot grim

# Setup serviços systemd
sudo ln -s $PWD/linux-agents-listen.service /etc/systemd/user/
sudo ln -s $PWD/openclaw-listen.service /etc/systemd/user/
systemctl --user daemon-reload
```

## Troubleshooting

### GUI automation não funciona

**Problema:** `scrot` retorna tela preta

**Causa:** Wayland vs X11 incompatibility

**Solução:** O código já tem fallback grim/scrot. Verificar:
```bash
which grim  # Deve estar instalado
which scrot # Deve estar instalado
```

### openclaw-listen não inicia

**Problema:** Porta 7610 já em uso

**Solução:**
```bash
pkill -f "openclaw-listen/main.py"
systemctl --user restart openclaw-listen
```

### Job falha com "Gateway agent failed"

**Problema:** Flag `--agent` faltando

**Solução:** Garantir que worker.py tem `--agent main`:
```python
cmd = ["openclaw", "agent", "--agent", "main", "--message", instruction]
```

## Desenvolvimento

### Adicionar novo comando GUI

```bash
cd rpi-gui/commands
cp template.py mycommand.py
# Edit mycommand.py
```

### Adicionar novo job server

Criar novo diretório com estrutura:
```
my-job-server/
├── main.py       # Entry point
├── worker.py     # Job worker
└── jobs/         # Job state
```

## Documentação Adicional

- **[OpenClaw Listen](../obsidian-vault/linux-agents/OpenClaw%20Listen.md)** - Documentação completa do job server recomendado
- **[Specs](./specs/)** - Especificações técnicas e testes
- **[Obsidian Vault](../obsidian-vault/)** - Notas de projeto e arquitetura

## Status

✅ **PRODUCTION READY**

- GUI automation funcionando
- Job servers estáveis
- API REST operational
- Testes E2E passando
- Serviços systemd configurados

## Roadmap

**Short-term:**
- [ ] Worker pool com concurrency limits
- [ ] Job priority queue
- [ ] Delivery integration para chat channels

**Long-term:**
- [ ] Web UI para job management
- [ ] Métricas/monitoring (Prometheus)
- [ ] Streaming results (SSE)
- [ ] Distributed job processing (Redis)

## Licença

MIT

## Contato

- **Projeto:** https://github.com/AlyssonM/linux-agents
- **Docs:** Obsidian vault (local)
