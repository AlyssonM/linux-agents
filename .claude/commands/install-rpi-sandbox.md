---
model: opus
description: Install, configure, and verify the linux-agents automation sandbox on Raspberry Pi (or any Linux ARM64 device)
---

# Purpose

Run directly on the Raspberry Pi device to install all dependencies, set up the environment, build tools, configure X11 display, and run a full verification suite that proves the sandbox is operational. This is the local bootstrap — run it on the machine that will execute agent jobs.

## Variables

RPI_JOB_PORT: 7600
DISPLAY_X11: ":1"

## Codebase Structure

```
linux-agents/
├── rpi-gui/          # Python CLI — GUI automation (pyatspi, xdotool, Tesseract)
├── rpi-term/         # Python CLI — Terminal automation (tmux)
├── rpi-job/          # Python — Job server (FastAPI)
├── rpi-client/       # Python — CLI client
├── .claude/
│   ├── commands/     # Slash commands
│   ├── skills/       # Agent skills (rpi-gui, rpi-term, rpi-job, rpi-client)
│   └── agents/       # System prompts
├── specs/            # E2E test specifications
└── artifacts/        # Test outputs and logs
```

## Manual Prerequisites

Before running this installer, the user **must** have a working Raspberry Pi OS setup:

| Requirement | Why | How |
|------------|-----|-----|
| **SSH Access** | Remote management | Enable SSH via `raspi-config` or boot folder |
| **X11 Display** | GUI automation requires X11 | Install and configure tightvnc on DISPLAY=:1 |
| **Python 3.11+** | Required for all tools | Usually pre-installed on Raspberry Pi OS |
| **Network** | Job server connectivity | Ensure Ethernet/Wi-Fi is configured |

### X11 Display Setup (Required for GUI Automation)

The agent sandbox needs an X11 display for GUI automation. On Raspberry Pi:

**Option 1: tightvnc (Recommended)**
```bash
# Install tightvncserver
sudo apt update
sudo apt install -y tightvncserver

# Start VNC server on display :1
vncserver :1 -geometry 1920x1080 -depth 24

# Set up startup script
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup <<EOF
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec openbox-session &
xterm &
EOF
chmod +x ~/.vnc/xstartup
```

**Option 2: X11 via local display**
```bash
# If you have a monitor connected, use :0
# Otherwise, use tightvnc :1 as above
```

**Verify X11 is working:**
```bash
export DISPLAY=:1
echo $DISPLAY
xhost +  # Allow local connections
```

**Before starting the workflow**, ask the user: "Do you have SSH access configured and an X11 display running (DISPLAY=:1 via tightvnc)? The verification checks will fail without these."

If the user says no or is unsure, show them the tables above and wait for confirmation before proceeding.

## Instructions

- All commands run locally via Bash — this is running ON the Raspberry Pi device
- Run each command individually so you can check the output before proceeding
- If a dependency is already installed, skip it and note the version
- If a step fails, stop and report the failure — do not continue blindly
- Use `apt` for system packages, `pip` or `uv` for Python packages
- Verify each tool works after installation by running its `--version` or `--help`
- The verification phase must test real functionality, not just that binaries exist
- Every verification check must produce a clear PASS or FAIL result

## Workflow

### Phase 1: System Check

1. Check OS and architecture:
   ```bash
   cat /etc/os-release
   uname -m
   ```

2. Check Python version:
   ```bash
   python3 --version
   ```
   Must be 3.11 or higher. If lower, inform user they need to upgrade.

3. Check what's already installed:
   ```bash
   which python3 pip uv tmux tesseract xdotool grim scrot xclip yq git
   ```
   Then for each found tool, run its version command:
   - `python3 --version`
   - `pip --version`
   - `uv --version` (if installed)
   - `tmux -V`
   - `tesseract --version`
   - `xdotool --version`
   - `grim --version` (Wayland)
   - `scrot --version` (X11)
   - `xclip --version`
   - `yq --version`
   - `git --version`

### Phase 2: Install Dependencies

4. Install system packages via apt:
   ```bash
   sudo apt update
   sudo apt install -y \
     python3 python3-pip python3-venv \
     tmux tesseract-ocr tesseract-ocr-eng \
     xdotool x11-apps x11-utils xterm \
     grim scrot xclip \
     yq git curl \
     libatk-bridge2.0-dev libatspi2.0-dev \
     python3-pyatspi
   ```

   Note: `libatk-bridge2.0-dev` and `libatspi2.0-dev` are required for pyatspi accessibility support.

5. Install uv (Python package manager) - faster than pip:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc  # or log out and back in
   ```

   If uv is already installed, skip this step.

### Phase 3: Clone and Setup Repository

6. Check if repo exists. If not, clone it:
   ```bash
   git clone https://github.com/AlyssonM/linux-agents.git ~/linux-agents
   cd ~/linux-agents
   ```

   If repo already exists, `cd` to it and pull latest:
   ```bash
   cd ~/linux-agents
   git pull origin main
   ```

7. Install Python dependencies for each tool using uv:
   ```bash
   cd rpi-gui && uv sync && cd ..
   cd rpi-term && uv sync && cd ..
   cd rpi-job && uv sync && cd ..
   cd rpi-client && uv sync && cd ..
   ```

   Or use pip if uv is not available:
   ```bash
   cd rpi-gui && pip install -e . && cd ..
   cd rpi-term && pip install -e . && cd ..
   cd rpi-job && pip install -e . && cd ..
   cd rpi-client && pip install -e . && cd ..
   ```

### Phase 4: Verify Installation

Run each check and record PASS/FAIL. Do not stop on failure — run all checks and report results at the end.

8. **rpi-gui** — verify CLI works:
    ```bash
    cd rpi-gui
    uv run python -m rpi_gui --help
    ```
    Expected: Output showing all commands (see, click, type, hotkey, scroll, drag, apps, screens, screenshot, ocr, focus, find, clipboard, wait)
    **Result:** PASS/FAIL

9. **rpi-term** — verify CLI works:
    ```bash
    cd rpi-term
    uv run python -m rpi_term --help
    ```
    Expected: Output showing all commands (session, run, send, logs, poll, fanout, proc)
    **Result:** PASS/FAIL

10. **rpi-job** — verify server can start:
    ```bash
    cd rpi-job
    timeout 5 uv run uvicorn rpi_job.main:app --port $RPI_JOB_PORT
    ```
    Expected: Server starts and logs "Uvicorn running" (timeout will kill it after 5 seconds)
    **Result:** PASS/FAIL

11. **rpi-client** — verify CLI works:
    ```bash
    cd rpi-client
    uv run python -m rpi_client --help
    ```
    Expected: Output showing all commands (start, status, list, stop, clear, logs)
    **Result:** PASS/FAIL

### Phase 5: GUI Automation Verification

Verify GUI automation works on X11 display.

12. **Display check** — verify X11 is accessible:
    ```bash
    export DISPLAY=$DISPLAY_X11
    xdpyinfo -display $DISPLAY_X11 | grep "dimensions"
    ```
    Expected: Output showing screen resolution (e.g., "1920x1080")
    **Result:** PASS/FAIL

13. **Screenshot test** — capture screen:
    ```bash
    cd rpi-gui
    uv run python -m rpi_gui screenshot --output /tmp/test-screenshot.png
    ```
    Expected: File `/tmp/test-screenshot.png` exists and is > 0 bytes
    **Result:** PASS/FAIL

14. **Accessibility test** — check pyatspi:
    ```bash
    python3 -c "import pyatspi; print('pyatspi OK')"
    ```
    Expected: Output "pyatspi OK"
    **Result:** PASS/FAIL

15. **OCR test** — verify Tesseract:
    ```bash
    tesseract --version
    echo "Hello World" | tesseract stdin stdout
    ```
    Expected: Tesseract version info + OCR output "Hello World"
    **Result:** PASS/FAIL

### Phase 6: End-to-End Verification

Test the full pipeline: submit job → execute → retrieve results.

16. **Start rpi-job server** in background:
    ```bash
    cd rpi-job
    uv run uvicorn rpi_job.main:app --port $RPI_JOB_PORT > /tmp/rpi-job.log 2>&1 &
    JOB_SERVER_PID=$!
    echo "Job server PID: $JOB_SERVER_PID"
    sleep 3  # Give it time to start
    ```
    Expected: Process is running (check with `ps -p $JOB_SERVER_PID`)
    **Result:** PASS/FAIL

17. **Submit test job**:
    ```bash
    cd rpi-client
    JOB_ID=$(uv run python -m rpi_client start http://localhost:$RPI_JOB_PORT "echo Hello World" --json | grep -o '"job_id": "[^"]*"' | cut -d'"' -f4)
    echo "Job ID: $JOB_ID"
    ```
    Expected: 8-character job ID (e.g., "a3f7b2c1")
    **Result:** PASS/FAIL

18. **Wait for completion**:
    ```bash
    sleep 3  # Give job time to complete
    STATUS=$(uv run python -m rpi_client status http://localhost:$RPI_JOB_PORT $JOB_ID --json | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    echo "Job status: $STATUS"
    ```
    Expected: Status is "done"
    **Result:** PASS/FAIL

19. **Retrieve results**:
    ```bash
    SUMMARY=$(uv run python -m rpi_client status http://localhost:$RPI_JOB_PORT $JOB_ID --json | grep -o '"summary": "[^"]*"' | cut -d'"' -f4)
    echo "Job summary: $SUMMARY"
    ```
    Expected: Summary contains "Hello World"
    **Result:** PASS/FAIL

20. **Cleanup**:
    ```bash
    kill $JOB_SERVER_PID
    rm /tmp/test-screenshot.png
    ```

### Final Summary

Report all verification results in a table:

| Check | Status | Notes |
|-------|--------|-------|
| rpi-gui CLI | PASS/FAIL | |
| rpi-term CLI | PASS/FAIL | |
| rpi-job server | PASS/FAIL | |
| rpi-client CLI | PASS/FAIL | |
| X11 display | PASS/FAIL | |
| Screenshot | PASS/FAIL | |
| pyatspi | PASS/FAIL | |
| Tesseract OCR | PASS/FAIL | |
| Job submission | PASS/FAIL | |
| Job execution | PASS/FAIL | |

If all checks PASS, the linux-agents sandbox is fully operational and ready to accept jobs! 🚀

If any checks FAIL, provide detailed error messages and troubleshooting steps.

## Troubleshooting

**X11 display not accessible:**
- Ensure tightvncserver is running: `vncserver :1`
- Check DISPLAY variable: `echo $DISPLAY`
- Test with simple X11 app: `xeyes`

**pyatspi import error:**
- Install accessibility dev packages: `sudo apt install libatk-bridge2.0-dev libatspi2.0-dev`
- Ensure at-spi-bus is running: `/usr/libexec/at-spi-bus-launcher`

**OCR fails silently:**
- Check Tesseract installation: `tesseract --version`
- Verify language data: `dpkg -l | grep tesseract-ocr`

**tmux session creation fails:**
- Install tmux: `sudo apt install tmux`
- Check tmux version: `tmux -V`

**rpi-job server won't start:**
- Check if port is in use: `netstat -tuln | grep $RPI_JOB_PORT`
- Verify dependencies: `cd rpi-job && uv sync`
- Check logs: `cat /tmp/rpi-job.log`
