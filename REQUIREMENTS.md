# Requirements & Environment

## System Requirements

### Hardware
- **Architecture:** ARM64 (tested on Raspberry Pi 4)
- **RAM:** 2GB+ (4GB recommended for GUI automation)
- **Storage:** 500MB+ free space

### Operating System
- **OS:** Debian-based Linux (Raspberry Pi OS, Ubuntu ARM64)
- **Display Server:** **X11 recommended** (Wayland has limitations - see below)

---

## Environment: X11 vs Wayland

### ✅ **RECOMMENDED: X11**

**Why X11?**
- Full GUI automation support
- `rpi-gui type` works perfectly
- `rpi-gui click` works perfectly
- Screenshot tools (scrot) native
- Proven in E2E tests

**Setup:**
```bash
# Configure LightDM for X11
sudo tee /etc/lightdm/lightdm.conf.d/50-x11-session.conf > /dev/null << 'EOF'
[Seat:*]
user-session=rpd-x.desktop
EOF

# Reboot
sudo reboot
```

**Verification:**
```bash
echo $XDG_SESSION_TYPE  # Should print: x11
```

---

### ⚠️ **LIMITED SUPPORT: Wayland**

**Current Status:**
- ✅ Screenshots: Works (via `grim`)
- ✅ OCR: Works
- ✅ Click: Returns success, but focus uncertain
- ❌ **Type: Known limitation - input routing fails via Xwayland**

**Technical Issue:**
```
Wayland → Xwayland → xdotool → Labwc compositor → App?
                                      ↓
                                  Input lost
```

**Workaround:**
Use X11 for GUI automation requiring type/click. Wayland is suitable for:
- Screenshots + OCR only
- Read-only operations
- Monitoring dashboards

---

## Installation

### Dependencies

#### GUI Automation (rpi-gui)
```bash
# X11 tools
sudo apt install -y scrot xdotool wmctrl xprop

# Wayland tools (if using Wayland)
sudo apt install -y grim slurp

# OCR
sudo apt install -y tesseract-ocr tesseract-ocr-eng

# Python dependencies
pip install -e ./rpi-gui
```

#### Terminal Automation (rpi-term)
```bash
# Terminal multiplexer
sudo apt install -y tmux

# Python dependencies
pip install -e ./rpi-term
```

#### Job Server (rpi-job + rpi-client)
```bash
# Python dependencies (includes FastAPI, httpx)
pip install -e ./rpi-job
pip install -e ./rpi-client
```

---

## Testing

### Quick Test

Test that your environment is ready:

```bash
# Test screenshot (X11)
scrot /tmp/test.png && file /tmp/test.png

# Test OCR
echo "hello" | tesseract -

# Test xdotool (X11 only)
xdotool type "test"  # Should work in X11

# Verify display
echo $DISPLAY  # Should be :0 or :1
```

### E2E Tests

Run the full test suite:

```bash
cd linux-agents
./specs/run-all-e2e.sh  # If script exists
```

Or run individual tests:
```bash
# See specs/ directory
cat specs/init-test.md
cat specs/gui-workflow.md
cat specs/terminal-integration.md
cat specs/job-server-workflow.md
```

---

## Known Issues

### Wayland Input Routing (Type)
- **Status:** Known limitation
- **Impact:** `rpi-gui type` does not work in Wayland sessions
- **Workaround:** Use X11 session
- **Tracking:** E2E Round 3 - gui-workflow test

### X11 Window Focus (Click)
- **Status:** Minor issue
- **Impact:** `rpi-gui focus` may not match window titles correctly
- **Workaround:** Use coordinate-based clicking
- **Severity:** Low - workflows still complete

### rpi-client latest -n ordering
- **Status:** Bug documented
- **Impact:** Returns oldest jobs instead of newest
- **Fix:** Sort by `created_at DESC` (TODO)

### rpi-job prompt validation
- **Status:** Bug documented
- **Impact:** Accepts whitespace-only prompts
- **Fix:** Add `if not prompt.strip(): reject` (TODO)

---

## Performance

### Benchmarks (Raspberry Pi 4, 4GB)

| Component | Metric | Value |
|-----------|--------|-------|
| Screenshot (scrot) | Time | ~0.3s |
| Screenshot (grim) | Time | ~0.4s |
| OCR (Tesseract) | Time | ~1.5s |
| Click (xdotool) | Time | ~0.1s |
| Type (xdotool) | Time | ~0.5s per 10 chars |

### Recommended Hardware

**Minimum:**
- Raspberry Pi 3B+
- 1GB RAM
- No GUI requirements (headless for rpi-job)

**Recommended:**
- Raspberry Pi 4 (4GB)
- 2GB+ RAM free
- X11 GUI session

---

## Troubleshooting

### "Can't open display" error

**Problem:** `scrot` or `xdotool` can't connect to display

**Solutions:**
```bash
# Check display is set
echo $DISPLAY

# Set display (X11)
export DISPLAY=:0

# For VNC sessions
export DISPLAY=:1
```

### display-manager.service not found

**Problem:** `systemctl status display-manager` returns unit not found on some systems.

**Cause:** `display-manager.service` is usually an alias. Some installations expose only the concrete service unit.

**Solutions:**
```bash
# Detect available display manager service
systemctl status display-manager || systemctl status lightdm || systemctl status gdm || systemctl status sddm

# Restart the service that exists
sudo systemctl restart display-manager || sudo systemctl restart lightdm || sudo systemctl restart gdm || sudo systemctl restart sddm
```

### OCR returns empty text

**Problem:** Screenshot is black or unreadable

**Solutions:**
- Ensure app is visible (not minimized)
- Check screenshot is not black: `file screenshot.png`
- For Wayland: Use `grim` instead of `scrot`

### wmctrl fails in Wayland

**Problem:** `_NET_CLIENT_LIST` not supported

**Solution:** This is expected in Wayland. Use:
- `rpi-gui apps` (limited)
- Coordinate-based operations
- Switch to X11 for full functionality

---

## Remote Access

### VNC Setup

#### X11 (tightvnc)
```bash
# Install
sudo apt install -y tightvncserver

# Start
vncserver :1 -geometry 1920x1080 -depth 24

# Connect
vncviewer <IP>:5901
```

#### Wayland (wayvnc)
```bash
# Install
sudo apt install -y wayvnc

# Start
wayvnc 0.0.0.0 5900

# Connect
vncviewer <IP>:5900
```

**Note:** For GUI automation testing, use tightvnc (X11) for full compatibility.

---

## Support

### Documentation
- `specs/` - E2E test specifications
- `*/README.md` - Component-specific docs
- `artifacts/e2e/` - Test results and evidence

### Issues
See "Known Issues" section above.
For new issues, check:
1. Environment: X11 vs Wayland
2. Display: `echo $DISPLAY`
3. Dependencies: `dpkg -l | grep tesseract`
