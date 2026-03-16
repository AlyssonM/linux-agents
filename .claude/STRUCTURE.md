# linux-agents Documentation Structure

This document describes the complete documentation structure for the linux-agents project, following the Mac Mini Agent pattern.

## Directory Structure

```
linux-agents/.claude/
├── agents/
│   └── job-system-prompt.md          # System prompt for job execution (workers)
└── commands/
    ├── prime.md                       # Load foundational context about the codebase
    ├── rpi-gui-term-user-prompt.md    # User prompt for GUI+Terminal automation tasks
    ├── install-rpi-sandbox.md         # Install and verify sandbox on Raspberry Pi
    └── install-engineer-workstation.md # Install and configure workstation
```

## Agents

### job-system-prompt.md

**Purpose:** System prompt loaded by the rpi-job worker process when executing jobs.

**Content:**
- Work tracking (updates, summary)
- Job YAML file management
- Cleanup procedures (tmux sessions, processes, temp files)
- Progress reporting workflow

**Usage:** Automatically loaded by worker.py when processing jobs via `yq` or Python YAML manipulation.

**Key Variables:**
- `{{JOB_ID}}` - Job identifier (8-character hex)
- Job file location: `linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml`

## Commands

### prime.md

**Purpose:** Load foundational context about the linux-agents codebase.

**When to use:** Start here to understand the architecture before working on any task.

**What it reads:**
1. Project overview (README.md, pyproject.toml)
2. Each tool's config (pyproject.toml files)
3. Skills documentation (.claude/skills/*)
4. Agent prompts (.claude/agents/*, .claude/commands/*)
5. Entry points (main.py, __init__.py)
6. E2E test specs (specs/*)

**Outcome:** Comprehensive understanding of:
- Architecture (4 tools)
- Stack (Python + pyatspi + xdotool + tmux + FastAPI)
- Key patterns (observe-act-verify, sentinel protocol, job YAML tracking)
- How pieces connect

### rpi-gui-term-user-prompt.md

**Purpose:** User prompt for GUI and Terminal automation tasks.

**When to use:** Agent receives a task requiring device control.

**Skills required:**
- rpi-gui (GUI automation)
- rpi-term (Terminal automation)

**Workflow:**
1. Observe first (rpi-gui see)
2. One action at a time (NEVER chain commands)
3. Read the output (parse JSON)
4. Verify after acting (rpi-gui see again)
5. Recover from failures
6. Clean up after yourself

**Critical Rules:**
- ONE command per bash call
- Always use `--json`
- Use OCR for Electron/Qt apps
- Use rpi-gui wait for timing
- Create tmux sessions before running commands
- Use DISPLAY=:1 (X11) for GUI automation

**Linux-specific:**
- X11 required for type/click (DISPLAY=:1)
- Wayland (DISPLAY=:0) only supports screenshots
- pyatspi for accessibility (may be incomplete)
- rpi-term proc for process management

### install-rpi-sandbox.md

**Purpose:** Install, configure, and verify the linux-agents sandbox on Raspberry Pi.

**When to use:** Initial setup of the Raspberry Pi device.

**Prerequisites:**
- SSH access configured
- X11 display running (DISPLAY=:1 via tightvnc)
- Python 3.11+
- Network connectivity

**Variables:**
- `RPI_JOB_PORT`: 7600 (default)
- `DISPLAY_X11`: ":1"

**Phases:**
1. System Check (OS, Python, existing packages)
2. Install Dependencies (apt packages, uv)
3. Clone and Setup Repository
4. Verify Installation (CLI tools work)
5. GUI Automation Verification (X11, screenshot, pyatspi, OCR)
6. End-to-End Verification (job server, submit job, retrieve results)

**Verification:**
| Check | Purpose |
|-------|---------|
| rpi-gui CLI | GUI automation tool works |
| rpi-term CLI | Terminal automation tool works |
| rpi-job server | Job server starts and listens |
| rpi-client CLI | Job client can submit jobs |
| X11 display | Display accessible for automation |
| Screenshot | Screen capture works |
| pyatspi | Accessibility API available |
| Tesseract OCR | Text recognition works |
| Job submission | Can submit jobs to server |
| Job execution | Jobs complete successfully |

**Output:** Table of PASS/FAIL results with troubleshooting steps.

### install-engineer-workstation.md

**Purpose:** Install and configure engineer's workstation to send jobs to the sandbox.

**When to use:** Setting up a laptop/desktop to control the Raspberry Pi.

**Variables:**
- `SANDBOX_HOST`: Raspberry Pi IP or hostname (required argument)
- `RPI_JOB_PORT`: 7600 (default)

**Prerequisites:**
- Python 3.11+
- Network connectivity to Raspberry Pi
- SSH access (optional but recommended)

**Phases:**
1. Install (Python, git, curl, uv)
2. Clone and Setup Repository
3. Verify (connectivity, job submission, result retrieval)
4. Configuration (environment variables)

**Verification:**
| Check | Purpose |
|-------|---------|
| Python 3.11+ | Compatible Python version |
| Git installed | Version control available |
| Network connectivity | Can reach Raspberry Pi |
| SSH connectivity (optional) | Can SSH into sandbox |
| rpi-client CLI | Job client works |
| Server reachable | rpi-job server responds |
| Job submission | Can submit jobs |
| Job completion | Jobs finish successfully |
| Result retrieval | Can get job output |
| Job listing | Can list all jobs |
| Environment configured | Convenience variables set |

**Usage Examples:**
```bash
# Simple command
rpi-client start "ls -la"

# Terminal automation
rpi-client start "rpi-term run test 'npm test'"

# GUI automation
rpi-client start "rpi-gui click --id B1"

# Check status
rpi-client status <job_id>
```

## Skills Documentation

See `.claude/skills/` directory:
- `rpi-gui/SKILL.md` - GUI automation (9.5 KB)
- `rpi-term/SKILL.md` - Terminal automation (7.0 KB)
- `rpi-job/SKILL.md` - Job server (6.1 KB)
- `rpi-client/SKILL.md` - Job client (6.7 KB)

## Key Differences from Mac Mini Agent

| Aspect | Mac Mini Agent | Linux Agents |
|--------|---------------|--------------|
| **GUI Automation** | Steer (Swift, AppKit) | rpi-gui (Python, pyatspi) |
| **Terminal Automation** | Drive (Python, tmux) | rpi-term (Python, tmux) |
| **Job Server** | Listen (FastAPI) | rpi-job (FastAPI) |
| **Job Client** | Direct (Click) | rpi-client (Click) |
| **Display** | macOS displays | X11 (:1) or Wayland (:0) |
| **Screenshot** | Native API | grim (Wayland) or scrot (X11) |
| **OCR** | Vision framework | Tesseract |
| **Input Simulation** | AppKit | xdotool |
| **Accessibility** | NSAccessibility | pyatspi |
| **Process Management** | macOS Activity Monitor | Linux /proc + ps |
| **Package Manager** | brew | apt |
| **Task Runner** | justfile | Direct CLI or scripts |

## Usage Workflow

### For New Setup

1. **Prime** the agent with context:
   ```
   /prime
   ```
   Agent reads: prime.md

2. **Install** the sandbox:
   ```
   /install-rpi-sandbox
   ```
   Agent reads: install-rpi-sandbox.md

3. **Install** the workstation:
   ```
   /install-engineer-workstation 192.168.1.100
   ```
   Agent reads: install-engineer-workstation.md

### For Automation Tasks

1. **Start** a GUI+Terminal automation task:
   ```
   /rpi-gui-term Open Chromium and navigate to example.com
   ```
   Agent reads: rpi-gui-term-user-prompt.md

2. **Monitor** job progress:
   ```bash
   rpi-client status <job_id>
   ```

3. **Retrieve** results:
   ```bash
   rpi-client status <job_id> --json | jq '.summary'
   ```

## Maintenance

- **Update documentation** when adding new commands or changing architecture
- **Keep commands in sync** with actual tool capabilities
- **Test installation commands** on fresh Raspberry Pi OS installs
- **Verify E2E tests** pass after any changes
- **Update this file** (STRUCTURE.md) when adding new documentation

## Related Files

- `README.md` - Project overview
- `specs/README.md` - E2E test documentation
- `obsidian-vault/linux-agents/` - User-facing documentation
- `memory/2026-03-16.md` - Development log
