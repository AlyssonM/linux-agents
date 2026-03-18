# Quick Start Guide

Get up and running with the Linux Agents stack in less than 5 minutes.

## 1. Environment Preparation

Ensure you are in an **X11 session** (required for GUI typing/clicking):
```bash
echo $DISPLAY          # Should be :0
echo $XDG_SESSION_TYPE # Should be x11
```

## 2. Installation

```bash
git clone https://github.com/AlyssonM/linux-agents.git
cd linux-agents

# Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install components
pip install -e apps/rpi-gui -e apps/rpi-term -e apps/rpi-job -e apps/rpi-client
```

## 3. Basic Usage Examples

### Terminal Control
```bash
# Start a persistent session
rpi-term session create --name dev-server

# Run commands
rpi-term run "python -m http.server 8080" --session dev-server
```

### GUI Interaction
```bash
# Capture screen and run OCR
rpi-gui see --ocr --json

# Click the center of the screen
rpi-gui click --x 960 --y 540 --json

# Type into the focused window
rpi-gui type "Hello from the AI" --enter --json
```

### File Transfer (LocalSend)
```bash
# Send the current screen to another device on the network
rpi-gui airdrop --target "Smartphone" --json
```

## 4. Running a Job Server

The job server allows you to queue tasks for different agents (Codex, Pi, OpenClaw).

```bash
# Start the server (runs on port 7610 by default)
cd apps/openclaw-listen
python main.py
```

In another terminal:
```bash
# Submit a job
rpi-client start http://localhost:7610 "Check system health and send report via LocalSend" --agent pi

# Check status
rpi-client list http://localhost:7610
```

## 5. Next Steps
- Review [REQUIREMENTS.md](REQUIREMENTS.md) for full system dependencies.
- Check the agents (.pi, .codex, .claude, .opencode)`skills/` directory for a complete command reference.
- For `secretctl` MCP + `pass`, read `.codex/skills/secretctl/SKILL.md`.
