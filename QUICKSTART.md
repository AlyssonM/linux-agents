# Quick Start (Linux ARM64 Agent Stack)

## 1) Setup

```bash
cd linux-agents
python3 -m venv .venv
source .venv/bin/activate
pip install -e rpi-gui[dev] -e rpi-term[dev] -e rpi-job[dev] -e rpi-client[dev]
```

## 2) Start job server

```bash
python -m rpi_job.main
```

## 3) Create and inspect a job

```bash
rpi-client start http://127.0.0.1:7600 "collect system info"
rpi-client list http://127.0.0.1:7600
rpi-client latest http://127.0.0.1:7600 -n 1
```

## 4) Terminal automation

```bash
rpi-term session create --name agent-1
rpi-term run --session agent-1 "echo hello"
rpi-term logs --session agent-1 --lines 50
```

## 5) GUI automation

```bash
rpi-gui see --ocr
rpi-gui click --x 400 --y 300
rpi-gui hotkey ctrl+s
```
