# Terminal and Browser E2E - Quick Start

Quick guide to run the `terminal-and-browser.md` E2E spec on Raspberry Pi 4.

## Prerequisites Check

```bash
# 1. Check X11 is running
DISPLAY=:1 xwininfo -root

# 2. Check tools installed
which chromium-browser rpi-gui rpi-term

# 3. Check tmux
tmux -V

# 4. Install missing tools
sudo apt install -y chromium-browser
```

## Quick Run

### Step 1: Start X11 (if needed)
```bash
tightvncserver :1 -geometry 1920x1080 -depth 24
export DISPLAY=:1
```

### Step 2: Create Terminal Session
```bash
rpi-term session create --name workspace
rpi-term send --session workspace "ls -la ~/Desktop"
rpi-term send --session workspace "date"
```

### Step 3: Take Screenshot
```bash
rpi-gui see --output /tmp/e2e-browser-screenshot.png
ls -lh /tmp/e2e-browser-screenshot.png
```

### Step 4: Open Browser
```bash
# Open Chromium
DISPLAY=:1 chromium-browser --no-sandbox --disable-gpu &
BROWSER_PID=$!

# Wait for load
sleep 5

# Navigate to URL (if needed, open new tab)
# Note: Command-line URL navigation in Chromium is limited
# You may need to use keyboard automation or manual interaction

# Take screenshot
rpi-gui see --output /tmp/e2e-chromium-screenshot.png

# Cleanup
kill $BROWSER_PID
```

### Step 5: Integration Test
```bash
# Download webpage in terminal
rpi-term send --session workspace "curl -s https://example.com | head -20"
rpi-term poll --session workspace --until "Example Domain"

# Save logs
rpi-term logs --session workspace > /tmp/e2e-terminal-output.txt
```

### Step 6: Cleanup
```bash
# Kill browser
pkill -9 chromium-browser

# Kill tmux session
rpi-term kill --session workspace

# Verify cleanup
ps aux | grep -E "(chromium|tmux)" | grep -v grep
```

## Expected Results

- ✅ Terminal session created
- ✅ Commands executed in tmux
- ✅ Screenshots captured
- ✅ Chromium opened and closed
- ✅ Integration (terminal + GUI) works

## Troubleshooting

### Chromium won't start
```bash
# Try with more flags
DISPLAY=:1 chromium-browser --no-sandbox --disable-dev-shm-usage --disable-gpu --disable-software-rasterizer &
```

### Screenshots are black
```bash
# Verify X11
DISPLAY=:1 xclock  # Should see a clock
```

### rpi-term can't find session
```bash
# List sessions
rpi-term session list
tmux list-sessions
```

## Full Spec

See [terminal-and-browser.md](./terminal-and-browser.md) for complete documentation.

## Runtime

- **Quick run:** ~3-5 minutes
- **Full spec with OCR:** ~8-10 minutes
- **Most time:** Chromium startup (slow on RPi)
