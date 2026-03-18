# Terminal and Browser Integration (Raspberry Pi)

## Overview
This E2E spec validates the integration of terminal automation (rpi-term) and GUI automation (rpi-gui) with browser control on a headless Raspberry Pi 4 running X11.

## Instructions
- As you work, keep notes in `/tmp/browser-integration-notes.txt`
- If you work longer than 5 minutes (based on your start time), wrap up and send what you have.
- Use DISPLAY=:0 (X11) for all GUI operations.

## Prerequisites
- X11 session running on DISPLAY=:0
- Chromium browser installed: `sudo apt install -y chromium-browser`
- tmux running for terminal sessions
- All agents installed: rpi-gui, rpi-term, rpi-client

## Environment Setup

### 1. Validate X11 Session (if not running)
```bash
export DISPLAY=:0
systemctl status display-manager || systemctl status lightdm || systemctl status gdm || systemctl status sddm
```

### 2. Verify Environment
```bash
echo "Display: $DISPLAY"
echo "Window manager:"
pgrep -a openbox || pgrep -a labwc
```

---

## Tasks

### Task 1: Terminal Automation with rpi-term
- [ ] Create a tmux session called `workspace` using rpi-term
- [ ] Run `ls -la ~/Desktop` and capture the output
- [ ] Run `date` and capture the timestamp
- [ ] Keep the session alive for later use

**Commands:**
```bash
rpi-term session create --name workspace
rpi-term send --session workspace "ls -la ~/Desktop"
rpi-term send --session workspace "date"
rpi-term poll --session workspace --until "Desktop"
```

**Expected Output:**
- Directory listing of ~/Desktop
- Current date/time

---

### Task 2: GUI Automation - Screenshot
- [ ] Use rpi-gui to take a screenshot of the current X11 desktop
- [ ] Save the screenshot to `/tmp/e2e-browser-screenshot.png`
- [ ] Verify the screenshot was created

**Commands:**
```bash
rpi-gui see --output /tmp/e2e-browser-screenshot.png
ls -lh /tmp/e2e-browser-screenshot.png
```

**Expected Output:**
- Screenshot file exists and is > 100KB
- File shows current X11 desktop state

---

### Task 3: Browser Automation - Open Chromium
- [ ] Open Chromium browser on X11
- [ ] Navigate to a test page (e.g., https://example.com or about:blank)
- [ ] Wait for page to load
- [ ] Take a screenshot of the browser window

**Commands (Method A - Direct X11):**
```bash
# Open Chromium in background
DISPLAY=:0 chromium-browser --no-sandbox --disable-gpu &
BROWSER_PID=$!

# Wait for browser to open
sleep 3

# Take screenshot
rpi-gui see --output /tmp/e2e-chromium-screenshot.png

# Cleanup
kill $BROWSER_PID
```

**Commands (Method B - Using xdotool for focus):**
```bash
# Open Chromium
DISPLAY=:0 chromium-browser --no-sandbox --disable-gpu &
BROWSER_PID=$!
sleep 3

# Try to focus the browser window (may require window ID)
rpi-gui window list > /tmp/windows.json
# Find chromium window ID and focus it
rpi-gui focus --exact <window-id>  # or use "chromium"

# Screenshot focused window
rpi-gui see --output /tmp/e2e-chromium-focused.png

# Cleanup
kill $BROWSER_PID
```

**Expected Output:**
- Chromium opens successfully
- Screenshot shows browser window
- Page content visible (example.com or about:blank)

---

### Task 4: Integration - Terminal + Browser
- [ ] From the tmux session, download a webpage using curl
- [ ] Capture the output
- [ ] Compare with what you see in the browser screenshot

**Commands:**
```bash
# From rpi-term session
rpi-term send --session workspace "curl -s https://example.com | head -20"
rpi-term poll --session workspace --until "Example Domain"

# Save terminal output
rpi-term logs --session workspace > /tmp/e2e-terminal-output.txt
```

**Expected Output:**
- HTML content from example.com
- Contains "Example Domain" title
- Matches what's visible in browser screenshot

---

### Task 5: OCR Validation (Optional)
- [ ] Take a screenshot of the browser window
- [ ] Use rpi-gui OCR to extract text from the screenshot
- [ ] Verify the text contains expected content

**Commands:**
```bash
# Take screenshot with OCR
rpi-gui see --output /tmp/e2e-ocr-test.png --ocr-json

# Read OCR results
cat /tmp/e2e-ocr-test.json | jq '.text' | head -10

# Verify expected text is present
cat /tmp/e2e-ocr-test.json | jq '.text' | grep -i "example"
```

**Expected Output:**
- OCR JSON file created
- Contains readable text from browser
- "Example" or "Domain" found in OCR output

---

## Deliverables

### 1. Text Report
Create `/tmp/e2e-browser-integration-report.md` containing:
- Directory listing from ~/Desktop
- Date/time from terminal session
- Description of browser screenshot (page loaded, visible elements)
- Terminal output from curl command
- Comparison between browser view and curl output
- Any issues encountered

### 2. Artifacts
- `/tmp/e2e-browser-screenshot.png` - Initial desktop screenshot
- `/tmp/e2e-chromium-screenshot.png` - Browser window screenshot
- `/tmp/e2e-terminal-output.txt` - Terminal session logs
- `/tmp/e2e-ocr-test.json` (optional) - OCR extraction results
- `/tmp/browser-integration-notes.txt` - Process notes

---

## Success Criteria

### Must Pass:
- ✅ rpi-term creates session and runs commands
- ✅ Terminal output captured correctly
- ✅ rpi-gui takes screenshots successfully
- ✅ Chromium opens on X11 without errors
- ✅ Browser screenshot shows web content
- ✅ Integration works (terminal + GUI coordination)

### Nice to Have:
- ✅ Window focus works (rpi-gui focus)
- ✅ OCR extracts readable text
- ✅ No process hangs or orphaned chromium instances

---

## Troubleshooting

### Issue: Chromium won't start
**Solution:**
```bash
# Check X11 is running
echo $DISPLAY
systemctl status display-manager || systemctl status lightdm || systemctl status gdm || systemctl status sddm

# Try with minimal flags
chromium-browser --no-sandbox --disable-dev-shm-usage --disable-gpu
```

### Issue: Screenshots are black/empty
**Solution:**
```bash
# Verify X11 session
DISPLAY=:0 xwininfo -root

# Use scrot directly
DISPLAY=:0 scrot /tmp/test-scrot.png
```

### Issue: Window focus doesn't work
**Solution:**
```bash
# List all windows
rpi-gui window list

# Use window ID instead of title
WINDOW_ID=$(rpi-gui window list | grep chromium | jq -r '.[0].id')
rpi-gui focus --exact "$WINDOW_ID"
```

### Issue: tmux session not found
**Solution:**
```bash
# List active sessions
rpi-term session list

# Check tmux directly
tmux list-sessions
```

---

## Cleanup

After completion:
```bash
# Kill chromium
pkill -9 chromium-browser

# Kill tmux session
rpi-term kill --session workspace

# Remove artifacts (optional)
rm -f /tmp/e2e-*.png /tmp/e2e-*.json /tmp/e2e-*.txt

# Verify cleanup
ps aux | grep -E "(chromium|tmux)" | grep -v grep
```

---

## Notes

### Key Differences from Mac Mini Agent
- **Terminal:** rpi-term (tmux-based) instead of Terminal.app
- **Browser:** Chromium on X11 instead of Safari
- **GUI:** rpi-gui (xdotool/scrot) instead of AppleScript
- **Display:** Native X11 (:0) instead of macOS desktop session
- **OCR:** Tesseract via rpi-gui instead of Vision framework

### Platform-Specific Considerations
- **X11 desktop session:** GUI automation targets DISPLAY=:0
- **ARM64 architecture:** Chromium performance may be slower
- **Wayland limitations:** Must use X11 for GUI automation (DISPLAY=:0)
- **Resource constraints:** 4GB RAM, browser may be slow to load

### Expected Runtime
- Setup: 1-2 minutes
- Terminal tasks: 1 minute
- Screenshot: 10 seconds
- Browser launch: 30-60 seconds (slow on RPi)
- OCR: 30-60 seconds
- Total: ~5-8 minutes

---

**Spec Version:** 1.0
**Last Updated:** 2026-03-16
**Environment:** Raspberry Pi 4, ARM64, X11 (:0)
