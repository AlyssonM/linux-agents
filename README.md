# Linux Agents

**Linux GUI + terminal automation for AI agents on Raspberry Pi and Linux ARM64. Direct your agents to see, type, click, orchestrate tmux, and execute remote jobs.**

<p align="center">
  <img src="assets/architecture-v3-animated.svg" alt="Linux Agents Architecture" width="100%"/>
</p>

AI agents are already good at writing code. The missing layer is **computer use on Linux**: seeing the desktop, operating apps, driving terminals, and exposing all of that through a remote job server.

**linux-agents** is our Linux/Raspberry Pi reinterpretation of the Mac Mini Agent idea: same autonomy goals, but adapted to **Python + X11 + tmux + FastAPI** on **ARM64 Linux**.

---

## The Problem

An agent that can only live in a terminal is still waiting on a human to:

- open the browser
- click buttons
- inspect UI state
- recover from unexpected screens
- coordinate multiple terminal sessions
- expose the machine as a remotely callable automation worker

On Linux, that gap is even more painful because:

- **Wayland often blocks synthetic input**, especially on headless or remotely accessed systems
- **Accessibility trees may be incomplete** depending on toolkit/app
- **Electron/Qt apps may require OCR fallback**
- **Terminal automation alone is not enough** for real end-to-end workflows

linux-agents closes that gap with four purpose-built tools.

---

## The Solution

> More and more software work will be delegated to agents — but the useful agents will be the ones that can actually operate a computer, not just generate text in a shell.

linux-agents gives AI agents practical control over a Linux device:

- **rpi-gui** — GUI automation on Linux/X11
- **rpi-term** — tmux-based terminal orchestration
- **rpi-job** — FastAPI job server for async execution
- **rpi-client** — CLI client for dispatch and monitoring

On top of that, the repo also includes two agent-oriented job layers:

- **listen + direct** — Codex-native async job flow
- **openclaw-listen** — OpenClaw-native async orchestration flow

This stack was validated on a **Raspberry Pi 4 (ARM64)** with a dual display strategy:

- **DISPLAY=:1 (X11 via tightvnc)** → full automation: type, click, screenshot, OCR
- **DISPLAY=:0 (Wayland)** → monitoring/screenshots only

Two control layers, four core CLIs, and complementary async agent runtimes. Linux-native agent autonomy.

---

## Who Is This For?

Engineers building:

- autonomous QA/test agents
- remote browser and desktop automation
- Raspberry Pi automation workers
- job-driven infrastructure helpers
- multi-step terminal + GUI workflows
- agent orchestration on low-cost ARM hardware

If your agent can write code but can’t ship, verify, click, or observe the UI — this is the missing layer.

---

## Tools

### rpi-gui — GUI Control

> Linux GUI automation CLI for AI agents. Eyes and hands on X11.

**Python** · pyatspi + xdotool + Tesseract

rpi-gui gives agents the ability to see, inspect, and interact with Linux desktop applications through screenshots, accessibility trees, OCR, and synthetic input.

<p align="center">
  <img src="assets/diagrams/steer-command-fan.svg" alt="rpi-gui command fan" width="600"/>
</p>

| Command     | Purpose |
| ----------- | ------- |
| `see`       | Capture screenshot + accessibility snapshot |
| `click`     | Click by coordinates or detected elements |
| `type`      | Type text into focused UI |
| `hotkey`    | Send keyboard shortcuts |
| `scroll`    | Scroll within apps or views |
| `drag`      | Drag from one point to another |
| `apps`      | List and inspect apps/windows |
| `screens`   | List displays and geometry |
| `window`    | Manage windows |
| `ocr`       | Extract text from the screen via Tesseract |
| `focus`     | Inspect current focus |
| `find`      | Locate elements by text/role |
| `clipboard` | Read/write clipboard |
| `wait`      | Wait for UI conditions |
| `screenshot`| Save screenshots directly |

#### OCR: The Equalizer on Linux

On Linux, accessibility support varies wildly across native, Electron, and Qt apps. OCR is the universal fallback that keeps the agent from going blind.

<p align="center">
  <img src="assets/diagrams/ocr-equalizer.svg" alt="OCR equalizer" width="700"/>
</p>

With `rpi-gui ocr --store`, visible text becomes addressable and actionable even when the accessibility tree is weak or empty.

**Important:** full GUI automation is validated on **X11**. On this project:

- `DISPLAY=:1` → ✅ type/click work
- `DISPLAY=:0` → ⚠️ screenshot/OCR only

---

### rpi-term — Terminal Control

> Terminal automation CLI for AI agents. Programmatic tmux control on Linux.

**Python** · tmux

rpi-term gives agents deterministic control over terminal sessions: create sessions, run commands, send input, inspect logs, poll for completion, fan out work, and manage spawned processes.

<p align="center">
  <img src="assets/diagrams/drive-command-flow.svg" alt="rpi-term command flow" width="450"/>
</p>

| Command   | Purpose |
| --------- | ------- |
| `session` | Create, list, and kill tmux sessions |
| `run`     | Execute command and wait for completion |
| `send`    | Send raw keystrokes |
| `logs`    | Capture pane output |
| `poll`    | Wait for output patterns |
| `fanout`  | Run commands across multiple sessions |
| `proc`    | Inspect and kill related processes |

#### The Sentinel Pattern

rpi-term uses sentinel markers to detect command completion reliably inside tmux panes.

<p align="center">
  <img src="assets/diagrams/sentinel-pattern.svg" alt="Sentinel pattern" width="700"/>
</p>

That makes terminal automation deterministic instead of “sleep and hope”.

---

### rpi-job — Job Server

> FastAPI job server for remote agent execution.

**Python** · FastAPI · YAML job state

rpi-job accepts jobs over HTTP, spawns workers, tracks state in YAML files, and exposes job progress/results to remote callers.

| Endpoint           | Purpose |
| ------------------ | ------- |
| `POST /job`        | Submit a new job |
| `GET /job/{id}`    | Get job status and result |
| `GET /jobs`        | List jobs |
| `POST /job/{id}/stop` | Stop a running job |
| `POST /jobs/clear` | Archive completed jobs |

**Current worker model:** direct shell/subprocess execution by default.

That means:

- fast
- cheap
- offline-friendly
- deterministic

LLM interpretation can be added later as an optional layer, but the current implementation deliberately keeps workers simple.

---

### rpi-client — Generic CLI Client

> CLI client for dispatching work to `rpi-job`.

**Python** · Click + httpx

rpi-client is the operator-facing entrypoint for sending generic jobs to the Raspberry Pi sandbox and retrieving results.

| Command  | Purpose |
| -------- | ------- |
| `start`  | Submit a new job |
| `status` | Get job state |
| `list`   | List all jobs |
| `stop`   | Stop a job |
| `clear`  | Archive finished jobs |
| `logs`   | Stream job updates |

Example:

```bash
rpi-client start http://192.168.0.24:7600 "echo hello"
rpi-client status http://192.168.0.24:7600 <job_id>
```

---

## Key Patterns

### Cross-App Pipelines

Combine terminal and GUI automation in the same workflow.

<p align="center">
  <img src="assets/diagrams/cross-app-pipeline.svg" alt="Cross-app pipeline" width="700"/>
</p>

Example flow:

```text
Open Chromium → navigate to app → run backend command in tmux → verify UI result via OCR
```

### Agent-on-Agent Orchestration

One agent can coordinate other tool-driven workflows through tmux sessions and remote jobs.

<p align="center">
  <img src="assets/diagrams/agent-inception.svg" alt="Agent inception" width="500"/>
</p>

### Multi-Window Orchestration

Agents can operate across browser, terminal, file manager, and desktop surfaces.

<p align="center">
  <img src="assets/diagrams/multi-window-tile.svg" alt="Multi-window orchestration" width="600"/>
</p>

### Self-Healing Automation

`wait`, `find`, `see`, `ocr`, `poll`, and `logs` allow the agent to recover instead of failing immediately on timing drift or UI differences.

<p align="center">
  <img src="assets/diagrams/self-healing-flow.svg" alt="Self-healing flow" width="700"/>
</p>

---

## Status

✅ **Validated on real hardware**

Tested on:

- **Raspberry Pi 4**
- **ARM64 Linux**
- **3.7 GB RAM usable**
- **X11 desktop via tightvnc on `:1`**

### E2E Results

**2026-03-16 overall status:** **95% pass rate**

- ✅ `init-test` — 87.5%
- ✅ `gui-workflow` — GREEN
- ✅ `terminal-integration` — GREEN
- ✅ `job-server-workflow` — GREEN
- ✅ `terminal-and-browser` — GREEN

This stack is not theoretical — it was exercised end-to-end on the target device.

---

## Quick Start

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y \
  tmux tesseract-ocr tesseract-ocr-eng \
  xdotool wmctrl scrot grim xclip \
  x11-apps x11-utils xterm
```

### 2. Install Python packages

```bash
cd linux-agents
python3 -m venv .venv
source .venv/bin/activate
pip install -e rpi-gui[dev] -e rpi-term[dev] -e rpi-job[dev] -e rpi-client[dev]
```

### 3. Use the correct display

```bash
export DISPLAY=:1
```

### 4. Try the tools

```bash
# GUI
rpi-gui see --ocr
rpi-gui type "hello world" --enter

# Terminal
rpi-term session create --name agent-1
rpi-term run --session agent-1 "uname -a"

# Job server
python -m rpi_job.main
rpi-client start http://127.0.0.1:7600 "echo ready"
```

---

## Project Structure

```text
linux-agents/
├── assets/              # Animated SVGs and diagrams
├── rpi-gui/             # GUI automation CLI
├── rpi-term/            # tmux terminal automation CLI
├── rpi-job/             # Generic FastAPI job server
├── rpi-client/          # Generic CLI client for rpi-job
├── listen/              # Codex-native agent job server
├── direct/              # Codex-native CLI client for listen
├── openclaw-listen/     # OpenClaw-native async job listener
├── specs/               # E2E specifications
├── artifacts/           # Test outputs
├── .claude/             # Claude-oriented agent scaffolding
└── .codex/              # Codex-oriented agent scaffolding
```

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** — fast setup
- **[REQUIREMENTS.md](REQUIREMENTS.md)** — environment and display requirements
- **[E2E-TEST-REPORT.md](E2E-TEST-REPORT.md)** — full test report
- **[TESTING-VALIDATION.md](TESTING-VALIDATION.md)** — validation summary
- **[FIXES-APPLIED.md](FIXES-APPLIED.md)** — bug fixes applied
- **[LOW-PRIORITY-ISSUES.md](LOW-PRIORITY-ISSUES.md)** — known limitations
- **[.claude/STRUCTURE.md](.claude/STRUCTURE.md)** — Claude agent structure
- **[.codex/STRUCTURE.md](.codex/STRUCTURE.md)** — Codex agent structure

---

## Custom Agent Support

These tools are **agent-agnostic** and can be used by:

- Claude Code
- Codex
- Gemini
- OpenCode
- custom agents
- any system that can invoke shell commands

The model does not matter. The control surface does.

---

## Releitura do Mac Mini Agent

linux-agents is explicitly inspired by **[disler/mac-mini-agent](https://github.com/disler/mac-mini-agent)** — but adapted to a very different target:

- **macOS → Linux ARM64**
- **Swift/AppKit/Vision → Python/pyatspi/xdotool/Tesseract**
- **single-device Mac workflows → Raspberry Pi remote worker workflows**
- **desktop-first Mac automation → dual-session Linux automation (`:0` + `:1`)**

This is not a copy. It is a Linux-native reinterpretation of the same core idea: give AI agents the ability to actually operate a real machine.

---

## License / Attribution

Inspired by the architecture and presentation patterns of Mac Mini Agent by [@disler](https://github.com/disler).

Implementation, Linux adaptation, Raspberry Pi validation, and job-oriented workflow design by this project.
