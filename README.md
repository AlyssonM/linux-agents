# Linux Agents Stack 🚀

Terminal and GUI Automation Stack for Linux ARM64 (Raspberry Pi 4), powered by OpenClaw.

**Keywords:** linux agents, ai agents, computer use, raspberry pi automation, x11 automation, gui automation, terminal automation, tmux automation, fastapi job server, ocr automation.
**Tags:** #linux #raspberrypi #aiagents #automation #x11 #gui #tmux #fastapi #ocr #openclaw

---

## 🏗️ Components

### 1. 🖥️ GUI Automation (`rpi-gui`)
- **Native X11 Support**: Mouse, keyboard, and window management via `xdotool` and `wmctrl`.
- **Intelligent Vision**: OCR support via Tesseract.
- **AirDrop for Linux**: Integrated `LocalSend` protocol for seamless file transfers between devices.
- **Commands**: `see`, `click`, `type`, `hotkey`, `scroll`, `drag`, `window`, `airdrop`, `send`.

### 2. 📟 Terminal Automation (`rpi-term`)
- **Tmux Integration**: Persistent, headless terminal sessions.
- **Interactive Mode**: `attach` command to open sessions in the GUI desktop (VNC).
- **Batch Processing**: `fanout` commands across multiple sessions.
- **Commands**: `session create/attach/kill/list`, `run`, `send`, `logs`, `poll`, `proc`, `fanout`.

### 3. 📥 Job Servers
- **`openclaw-listen`**: REST API server for openclaw sub-agent execution with full state management.
- **`listen` (Recommended)**: High-level agent runtime (Codex/Pi/Opencode).
- **`rpi-job`**: Lightweight subprocess-based job runner.

---

## 🛠️ Installation & Setup

### Prerequisites
- **OS**: Debian-based (Raspberry Pi OS / Ubuntu ARM64).
- **Environment**: X11 (DISPLAY=:0) is required for full GUI interaction.

### Quick Install
```bash
git clone https://github.com/AlyssonM/linux-agents.git
cd linux-agents
python3 -m venv .venv
source .venv/bin/activate

# Install all components in editable mode
pip install -e apps/rpi-gui -e apps/rpi-term -e apps/rpi-job -e apps/rpi-client
```

---

## 🚀 Quick Start

### 1. Terminal Automation
```bash
# Create a session
rpi-term session create --name my-task

# Run a command and wait for output
rpi-term run "ls -la" --session my-task --json

# See it happening in the GUI
rpi-term session attach --name my-task
```

### 2. GUI Automation
```bash
# Look at the screen (saves to /tmp)
rpi-gui see --ocr --json

# Transfer a screenshot to your phone
rpi-gui airdrop --target "MyPhone" --json
```

### 3. Job Server (REST API)
```bash
# Start the server
cd apps/listen && python main.py

# Submit a job via CLI
rpi-client start http://localhost:7600 "Write a python script to monitor CPU" --agent pi
```

---

## 📝 Documentation

- [QUICKSTART.md](QUICKSTART.md): Detailed 5-minute guide.
- [REQUIREMENTS.md](REQUIREMENTS.md): System dependencies and X11 vs Wayland guide.
- [SPECS/](specs/): Architecture and E2E workflow specifications.
- [SKILLS/](.pi/skills/): Detailed API reference for each CLI tool.

---

## ⚙️ Deployment (Systemd)

Service templates are available in `templates/systemd/`. To install:
1. Copy the `.template` file to `/etc/systemd/system/`.
2. Replace `{{USER}}`, `{{WORKING_DIRECTORY}}`, and `{{PYTHON_VENV}}` with your actual paths.
3. Run `sudo systemctl enable --now <service-name>`.

---

## 🙌 Inspiration

This project is inspired by [mac-mini-agent](https://github.com/disler/mac-mini-agent), adapting the computer-use agent model to Linux ARM64 and Raspberry Pi workflows.

---

## 🛡️ License
MIT License. Created with ❤️ for the Raspberry Pi ecosystem.
