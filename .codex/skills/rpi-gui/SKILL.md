---
name: rpi-gui
description: Linux GUI automation CLI for AI agents. Use rpi-gui to see the screen, click elements, type text, send hotkeys, scroll, drag, run OCR on any app, take screenshots, and wait for UI conditions. Works with X11 (DISPLAY=:0) for full automation.
---

# rpi-gui — Linux GUI Automation

Run from: `cd linux-agents/rpi-gui && rpi-gui <command>`

Run `rpi-gui --help` and `rpi-gui <command> --help` to learn each command's flags.

## Commands

### see — Look at the screen

```bash
rpi-gui see --json
rpi-gui see --ocr --json
rpi-gui see --output /tmp/screen.png --json
```

Capture screen and optionally run OCR.

### click — Click on screen

```bash
rpi-gui click --x 100 --y 200 --json
rpi-gui click --text "Submit" --json
rpi-gui click --x 100 --y 200 --button right --json
```

### type — Type text

```bash
rpi-gui type "Hello World" --json
rpi-gui type "https://google.com" --enter --json
rpi-gui type "secret" --interval 0.1 --json
```

### hotkey — Press shortcuts

```bash
rpi-gui hotkey ctrl+c --json
rpi-gui hotkey alt+tab --json
rpi-gui hotkey ctrl+alt+t --json
```

### scroll — Scroll screen

```bash
rpi-gui scroll up 5 --json
rpi-gui scroll down 2 --json
```

### drag — Drag and drop

```bash
rpi-gui drag --from "100,200" --to "300,400" --json
```

### window — Manage windows

```bash
rpi-gui window list --json
rpi-gui window move --target "Chromium" --x 0 --y 0 --json
rpi-gui window maximize --target "Chromium" --json
```

### focus — Focus window

```bash
rpi-gui focus "Chromium" --json
rpi-gui focus "Visual Studio Code" --exact --json
```

### airdrop / send — LocalSend file transfer

```bash
rpi-gui airdrop --json                              # Screenshot and send to auto-discovered device
rpi-gui airdrop --target "iPhone" --json            # Send to specific device
rpi-gui send --file /tmp/doc.pdf --json             # Send specific file
rpi-gui send --screenshot --json                    # Same as airdrop
```

Use for "AirDrop-like" transfers to your phone or computer.

## Environment Setup

**Required: X11 Display (DISPLAY=:0)**

```bash
export DISPLAY=:0
```

## Rules

- **One action, then observe** — Always run `see` after an action to verify.
- **Always use `--json`** for structured output.
- **Write files to /tmp** — Output images or logs should go to `/tmp/`.
- **Focus first** — Ensure the window is focused before typing or clicking text.
