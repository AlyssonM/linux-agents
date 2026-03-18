# Specs Directory

End-to-end test specifications for the Linux ARM64 automation toolkit.

## Available Specs

### Core E2E Tests
- **[init-test.md](./init-test.md)** - Initial setup and basic functionality validation
- **[gui-workflow.md](./gui-workflow.md)** - GUI automation workflow (type, click, screenshot, OCR)
- **[terminal-integration.md](./terminal-integration.md)** - Terminal automation with tmux integration
- **[job-server-workflow.md](./job-server-workflow.md)** - Job server (FastAPI) and client integration

### Integration Tests
- **[terminal-and-browser.md](./terminal-and-browser.md)** ⭐ NEW - Terminal + Browser integration test
  - Validates rpi-term + rpi-gui integration
  - Tests Chromium browser on X11
  - OCR validation
  - Cross-platform coordination

### Documentation
- **[TEMPLATE.md](./TEMPLATE.md)** - Template for creating new E2E specs

## Running Specs

### Quick Start
```bash
# Activate environment
cd linux-agents
source .venv/bin/activate

# Set X11 display
export DISPLAY=:0

# Run a spec (follow the tasks)
# Example: terminal-and-browser
cat specs/terminal-and-browser.md
```

### Recommended Execution Order
1. **init-test.md** - Verify basic installation
2. **gui-workflow.md** - Test GUI automation
3. **terminal-integration.md** - Test terminal automation
4. **job-server-workflow.md** - Test job server
5. **terminal-and-browser.md** - Test full integration

## Test Results

**Latest Results (2026-03-16):**

| Spec | Status | Pass Rate | Environment | Runtime |
|------|--------|-----------|-------------|---------|
| init-test | ✅ PASS | 87.5% | X11 | - |
| gui-workflow | ✅ GREEN | 100% | X11 | 4m 27s |
| terminal-integration | ✅ GREEN | 100% | X11 | 4m 27s |
| job-server-workflow | ✅ GREEN | 100% | Headless | 6m 41s |
| terminal-and-browser | ✅ GREEN | 100% | X11 | 2m 44s |

**Overall:** 95% pass rate (94.3% including all tests)

## Creating New Specs

1. Copy [TEMPLATE.md](./TEMPLATE.md)
2. Define tasks and success criteria
3. Include cleanup steps
4. Add troubleshooting section
5. Test on X11 environment

## Environment Requirements

### Required
- **Python:** 3.11+
- **Display:** X11 (DISPLAY=:0)
- **Tools:** rpi-gui, rpi-term, rpi-client, rpi-job

### Optional (for specific specs)
- **Browser:** Chromium (for terminal-and-browser)
- **OCR:** Tesseract (for OCR tests)
- **Window manager:** openbox (for window management tests)

## Artifact Storage

Test artifacts are stored in:
```
../artifacts/e2e/YYYYMMDD-HHMM/
├── screenshots/
├── logs/
├── reports/
└── final-report.md
```

## Quick Reference

### GUI Commands
```bash
rpi-gui see --output screenshot.png
rpi-gui type "hello world"
rpi-gui click --x 100 --y 200
rpi-gui window list
```

### Terminal Commands
```bash
rpi-term session create --name test
rpi-term send --session test "ls -la"
rpi-term poll --session test --until "done"
rpi-term logs --session test
```

### Job Server Commands
```bash
python -m rpi_job.main &
rpi-client start http://127.0.0.1:7600 "test job"
rpi-client latest http://127.0.0.1:7600 -n 1
```

## Troubleshooting

### Common Issues

**DISPLAY not set:**
```bash
export DISPLAY=:0
```

**X11 not running:**
```bash
systemctl status display-manager || systemctl status lightdm || systemctl status gdm || systemctl status sddm
sudo systemctl restart display-manager || sudo systemctl restart lightdm || sudo systemctl restart gdm || sudo systemctl restart sddm
```

`display-manager.service` is a generic systemd alias used by many distros. If the alias is not present, use the real service name (`lightdm`, `gdm`, or `sddm`) for your environment.

**tmux session exists:**
```bash
rpi-term kill --session <name>
tmux kill-session -t <name>
```

**Chromium won't start:**
```bash
# Use minimal flags
chromium-browser --no-sandbox --disable-gpu --disable-dev-shm-usage
```

See [../REQUIREMENTS.md](../REQUIREMENTS.md) for more troubleshooting.

---

**Last Updated:** 2026-03-16
**Maintainer:** Arpie (Linux ARM64 Agents)
