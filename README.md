# Linux Agents

<div align="center">

<!-- Animated SVGs -->
<img src="assets/architecture-v3-animated.svg" width="100%" alt="Raspberry Pi" />

**Projeto de automação para Linux (Raspberry Pi 4) usando OpenClaw AI agent framework**

[![Status](https://img.shields.io/badge/status-production--ready-success)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![RaspberryPi](https://img.shields.io/badge/rpi-4-red.svg)](https://www.raspberrypi.com)
[![GUI](https://img.shields.io/badge/gui-automation-blue.svg)](https://github.com)
[![Terminal](https://img.shields.io/badge/terminal-tmux-green.svg)](https://github.com)

</div>

---

## 🚀 Visão Geral

Este projeto contém agentes de automação para Linux, incluindo GUI automation, terminal automation, e job processing.

**Status do projeto:** ✅ **PRODUCTION READY**

---

## 📦 Componentes

### Core Agents

#### **`rpi-gui/`** - GUI Automation para Linux

Automação de interface gráfica (X11/Wayland):

- ✅ Screenshot capture (PIL/pyautogui)
- ✅ OCR (tesseract)
- ✅ Mouse/keyboard automation (xdotool)
- ✅ Window management (wmctrl)
- ✅ **LocalSend integration** (AirDrop-like file transfer) ⭐ **NOVO!**

**Comandos principais:**
```bash
# Capturar tela
rpi-gui see --output screenshot.png

# Mouse/keyboard
rpi-gui click --x 100 --y 200
rpi-gui type --text "Hello, World!"

# **NOVO: LocalSend**
rpi-gui send --screenshot --target "iPhone"
rpi-gui airdrop --target "Pixel 8"
```

📖 **Docs:** [LocalSend Guide](../../memory/localsend-complete-guide.md)

---

#### **`rpi-term/`** - Terminal Automation

Automação de terminal via tmux:

- ✅ Criar sessões tmux headless
- ✅ Enviar comandos para sessões
- ✅ Capturar output de sessões
- ✅ **Comando attach** (abre lxterminal no VNC) ⭐ **NOVO!**

**Comandos principais:**
```bash
# Criar sessão
rpi-term session create --name agent-1

# **NOVO: Anexar no VNC**
rpi-term session attach --name agent-1 --geometry 900x600

# Enviar comandos
rpi-term send --session agent-1 "npm test"

# Capturar output
rpi-term logs --session agent-1
```

📖 **Docs:** [tmux Control](../../.npm-global/lib/node_modules/openclaw/skills/tmux/SKILL.md)

---

#### **`rpi-job/`** - Simple Job Server

Servidor de jobs simples baseado em subprocess:

- ✅ Shell script jobs
- ✅ YAML job state
- ✅ Systemd service

**Status:** ✅ Stable

---

#### **`listen/`** - External Agent Runtime

Runtime de agentes externos via Codex:

- ✅ `codex exec` + tmux integration
- ✅ Job state management
- ✅ Systemd service

**Status:** ✅ Stable

---

#### **`openclaw-listen/`** - OpenClaw-Native Job Server ⭐ **RECOMMENDED**

Servidor de jobs REST API nativo OpenClaw:

- ✅ REST API para submissão de jobs
- ✅ Execução de subagentes (subprocess isolado)
- ✅ YAML job state
- ✅ Systemd service

**Quick start:**
```bash
cd openclaw-listen
python main.py
```

**Criar job via API:**
```bash
curl -X POST http://localhost:7610/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "List files in current directory",
    "execution": {"strategy": "auto", "timeout_seconds": 30}
  }'
```

📖 **Docs:** [OpenClaw Listen](../../obsidian-vault/linux-agents/OpenClaw%20Listen.md)

**Status:** ✅ Production-ready

---

## 🏗️ Arquitetura

```
linux-agents/
├── rpi-gui/              # GUI automation commands
│   ├── commands/         # Individual command modules
│   ├── modules/          # Shared utilities
│   │   └── localsend.py  # ⭐ LocalSend integration
│   └── cli.py            # CLI entry point
│
├── rpi-term/             # Terminal automation via tmux
│   ├── commands/         # tmux session commands
│   │   └── session.py    # ⭐ NEW: attach command
│   └── modules/          # tmux wrapper
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
│   ├── gui-workflow.md   # GUI automation tests
│   ├── terminal-and-browser.md
│   └── openclaw-listen-architecture.md
│
└── README.md             # This file
```

---

## 🔄 Serviços Systemd

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

---

## 📊 Comparação de Job Servers

| Componente | Tecnologia | Isolamento | API REST | Recomendado |
|------------|-----------|-------------|----------|-------------|
| **rpi-job** | subprocess shell | Baixo | ❌ | Simples |
| **listen** | `codex exec` + tmux | Médio | ❌ | Integrado |
| **openclaw-listen** | OpenClaw agent CLI | Alto | ✅ | ⭐ **SIM** |

---

## 🎯 Quick Start

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
python -m rpi_gui.cli see
python -m rpi_gui.cli type --text "Hello, World!"

# ⭐ LocalSend
python -m rpi_gui.cli send --screenshot
```

### 3. Testar terminal automation

```bash
cd rpi-term
.venv/bin/pip install -e .

# Criar e anexar sessão
.venv/bin/rpi-term session create --name test
.venv/bin/rpi-term session attach --name test
```

### 4. Iniciar openclaw-listen server

```bash
cd openclaw-listen
python main.py
```

---

## 🧪 Testes E2E

Rodar suite de testes completa:

```bash
cd specs
./run-e2e-tests.sh
```

---

## 📚 Documentação Adicional

### GUI Automation
- [LocalSend Complete Guide](../../memory/localsend-complete-guide.md) ⭐ **NOVO**
- [GUI Workflow Tests](specs/gui-workflow.md)
- [OCR Commands](rpi-gui/README.md)

### Terminal Automation
- [tmux Session Control](../../.npm-global/lib/node_modules/openclaw/skills/tmux/SKILL.md)
- [Terminal Integration Tests](specs/terminal-and-browser.md)

### Job Servers
- [OpenClaw Listen Architecture](specs/openclaw-listen-architecture.md)
- [Job Processing](../../memory/jobs.md)

### System Configuration
- [Daily Summary - 2026-03-17](../../memory/2026-03-17-daily-summary.md) ⭐ **NOVO**
- [VNC Configuration](../../memory/2026-03-17-vnc.md)
- [X11 Migration](../../memory/2026-03-17-migracao-x11.md)

---

## 🆕 Novidades (Março 2026)

### rpi-gui

- ✅ **LocalSend integration** - Comandos `send` e `airdrop`
- ✅ Descoberta automática de dispositivos
- ✅ Upload via HTTPS
- ✅ Testado com Windows

### rpi-term

- ✅ **Comando `attach`** - Abre lxterminal no VNC
- ✅ Geometria configurável
- ✅ Display configurável

### Sistema

- ✅ **VNC production-ready** - x11vnc configurado
- ✅ **Desktop otimizado** - openbox + tint2
- ✅ **Economia de RAM** - ~150MB poupados
- ✅ **OCR otimizado** - Texto branco em barra preta

---

## 📈 Performance

| Métrica | Valor |
|---------|-------|
| Uso RAM (idle) | ~70MB |
| Economia (vs Wayland) | ~150MB |
| Resolução VNC | 1920x1080 |
| Comandos rpi-gui | 15+ |
| Comandos rpi-term | 8+ |

---

## 🤝 Contribuindo

Este projeto está em desenvolvimento ativo. Sugestões e PRs são bem-vindas!

---

## 📄 Licença

MIT License - veja arquivo LICENSE para detalhes.

---

<div align="center">

**Desenvolvido com ❤️ para Raspberry Pi 4**

[⬆ Voltar ao topo](#linux-agents)

</div>
