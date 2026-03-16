---
name: rpi-gui
description: Linux GUI automation CLI for AI agents. Use rpi-gui to see the screen, click elements, type text, send hotkeys, scroll, drag, run OCR on any app, take screenshots, and wait for UI conditions. Works with X11 (DISPLAY=:1) for full automation.
---

# rpi-gui — Linux GUI Automation

Run from: `cd linux-agents/rpi-gui && rpi-gui <command>`

Run `rpi-gui --help` and `rpi-gui help <command>` to learn each command's flags before using it.

## Commands

| Command     | Purpose                                                                                                                                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `see`       | Takes a screenshot (PNG) and walks the accessibility tree via pyatspi. Screenshot always succeeds. Elements are best-effort — may be empty for some apps. Pass `--ocr` to fall back to Tesseract OCR when the tree is empty. |
| `click`     | Click by element ID, label, or coordinates (via xdotool)                                                                                                                                                                 |
| `type`      | Type text into focused element or a target (via xdotool)                                                                                                                                                                 |
| `hotkey`    | Keyboard shortcuts (ctrl+s, return, escape, etc.)                                                                                                                                                           |
| `scroll`    | Scroll up/down/left/right                                                                                                                                                                                  |
| `drag`      | Drag between elements or coordinates                                                                                                                                                                       |
| `apps`      | List running windows/applications                                                                                                                                                                             |
| `screens`   | List displays with resolution and scale                                                                                                                                                                    |
| `screenshot`   | Take screenshot and save to file (supports grim for Wayland, scrot for X11)                                                                                                                                                          |
| `ocr`       | Takes a screenshot and runs Tesseract OCR on it. Returns text with x/y positions. Use `--store` to make results clickable (O1, O2, etc.). Use when `see` returns no elements.                                 |
| `focus`     | Show currently focused window/element                                                                                                                                                                             |
| `find`      | Search elements by text in latest snapshot                                                                                                                                                                 |
| `clipboard` | Read/write X clipboard (via xclip)                                                                                                                                                                                |
| `wait`      | Wait for window launch or element to appear                                                                                                                                                                   |

Always pass `--json` for structured output.

## Environment Setup

**Required: X11 Display (DISPLAY=:1)**

rpi-gui requires X11 for full automation functionality. On Raspberry Pi:

```bash
# Use X11 display (tightvnc)
export DISPLAY=:1

# For Wayland displays (DISPLAY=:0), only screenshots work
# Type/click do NOT work in Wayland
```

## How to Work

You are controlling a real Linux desktop. You cannot see anything unless you explicitly look. You cannot assume anything worked unless you verify.

### 1. Know your environment first

Before doing anything, understand the display setup, what's running, and capture the current state:

```bash
rpi-gui screens --json       → which monitors exist, their resolution
rpi-gui apps --json          → what windows/apps are running
rpi-gui see --screen 0 --json  → screenshot of screen 0 (primary)
rpi-gui screenshot --output /tmp/screen.png  → save screenshot to file
```

Take a screenshot of **each screen** returned by `rpi-gui screens`. Read them. This gives you a baseline of the desktop before you start making changes.

### 2. Focus the app, then verify

Before interacting with any app, make sure it's the active window:

```bash
rpi-gui apps activate Chromium --json
rpi-gui see --app Chromium --json        → verify it's in front, read the state
```

### 3. One action, then observe

**NEVER chain multiple rpi-gui commands in one bash call.** The screen changes after every action. You must look after every action.

The loop is:

1. `rpi-gui see` — look at the screen
2. Read the JSON — understand what you see
3. Do ONE action (click, type, hotkey, scroll)
4. `rpi-gui see` — look again to confirm it worked
5. Repeat

### 4. Clicking safely

Before clicking anything:

- Run `rpi-gui see --app <app> --json` to get a fresh snapshot
- Use element IDs from the snapshot (B1, T1, L3) — not coordinates when possible
- If using coordinates, they are **relative to the screenshot image**, factor in window position
- After clicking, run `rpi-gui see` again to confirm the click landed

### 5. Typing into fields

- Before typing anything: ALWAYS check focus with `rpi-gui focus --json` to confirm the right element is targeted.
  - If you're not focused on the right element, use `rpi-gui apps activate <AppName> --json` to switch apps or `rpi-gui click` to focus the correct field.
  - Then validate your focus with `rpi-gui focus --json`
- Use `rpi-gui type "text" --into T1 --json` to click-then-type in one step when targeting a specific field
- If typing into the already-focused element, just `rpi-gui type "text" --json`
- After typing, verify with `rpi-gui see` that the text appeared correctly
- For URLs in browsers: type the URL, then `rpi-gui hotkey return --json`, then `rpi-gui see` to confirm navigation

### 6. Reading content from apps

Both `see` and `ocr` save a screenshot PNG. The path is in the JSON output under `"screenshot"`. You can read this image file to visually inspect what's on screen.

**Native apps** (Chromium, Firefox, Terminal): `rpi-gui see --app <name> --json` gives you the accessibility tree with labeled elements via pyatspi. If the element list is empty, the screenshot still exists — read it or try `--ocr` to fall back.

**Electron/Qt apps**: Accessibility trees may be empty. Use OCR instead:

```bash
rpi-gui ocr --app "VS Code" --store --json
```

With `--store`, OCR results become clickable elements (O1, O2, etc.).

**Web pages**: Accessibility tree may be shallow. Use `rpi-gui ocr --app Chromium --json` to read all visible text with positions. Use the positions to click precisely.

### 7. Waiting for things

Don't assume the UI is ready after an action. Use `rpi-gui wait` or run `rpi-gui see` in a loop:

```bash
rpi-gui wait --app Chromium --json                     → wait for app to launch
rpi-gui wait --for "Submit" --app Chromium --json      → wait for element to appear
```

### 8. Display environments

**X11 (DISPLAY=:1 - tightvnc):**
- ✅ Full automation support (click, type, see, ocr)
- ✅ Recommended for automation
- ✅ Desktop environment: openbox

**Wayland (DISPLAY=:0 - wayvnc):**
- ⚠️  Only screenshots work (grim)
- ❌ Type/click DO NOT work
- ⚠️  Use for monitoring only

## Element IDs

Elements from `rpi-gui see` get role-based IDs: **B** (button), **T** (text entry), **S** (static text), **I** (image), **C** (checkbox), **L** (link), **M** (menu item), **O** (OCR element), etc.

IDs regenerate with each snapshot. Always use IDs from the most recent `rpi-gui see` or `rpi-gui ocr --store`.

## Key Differences from macOS Steer

- **pyatspi** instead of macOS Accessibility API
- **xdotool** instead of AppKit for input simulation
- **Tesseract** instead of Vision framework for OCR
- **X11/Wayland** display environments instead of macOS displays
- **xclip** for clipboard instead of macOS NSPasteboard

## Rules

- **One command per bash call** — never chain rpi-gui commands
- **Always verify** — `rpi-gui see` after every action
- **Focus first** — activate the app before interacting
- **Know your screens** — check `rpi-gui screens` before clicking
- **Use `--json` always** — structured output is reliable
- **Write all files to /tmp** — never write output files into the project directory
- **Use DISPLAY=:1 for X11 automation** — type/click only work in X11
- **Run `rpi-gui help <cmd>`** if you're unsure about a command's flags
