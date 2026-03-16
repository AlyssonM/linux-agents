---
name: rpi-term
description: Terminal automation CLI for AI agents. Use rpi-term to create tmux sessions, execute commands, send keystrokes, read output, poll for patterns, run commands in parallel across sessions, and manage processes. Always use --json for structured output.
---

# rpi-term — Terminal Automation via tmux

Run from: `cd linux-agents/rpi-term && rpi-term <command>`

rpi-term gives you full programmatic control over tmux sessions — creating terminals, running commands, reading output, and orchestrating parallel workloads.

## Commands

### session — Manage tmux sessions

```bash
rpi-term session create agent-1 --json                     # Opens a tmux session (headed)
rpi-term session create agent-1 --window build --json      # Named window, headed
rpi-term session create agent-1 --detach --json            # Headless (no window)
rpi-term session list --json                                # List all sessions
rpi-term session kill agent-1 --json                        # Kill a session
```

**Default is headed** — a new tmux window opens. Use `--detach` when you explicitly need a headless session.

### run — Execute command and wait for completion

Uses sentinel protocol (`__DONE_<token>:<exit_code>`) for reliable completion detection.

```bash
rpi-term run agent-1 "npm test" --json                     # Run and wait
rpi-term run agent-1 "make build" --timeout 120 --json     # Custom timeout
rpi-term run agent-1 "ls" --pane 1 --json                  # Target specific pane
```

Returns: exit code, captured output between sentinels.

### send — Raw keystrokes (no completion waiting)

For interactive tools (vim, ipython, etc.) where sentinel detection would interfere.

```bash
rpi-term send agent-1 "vim file.txt" --json                # Send command
rpi-term send agent-1 ":wq" --json                         # Send vim command
rpi-term send agent-1 "y" --no-enter --json                # Send without Enter
```

### logs — Capture pane output

```bash
rpi-term logs agent-1 --json                               # Current pane content
rpi-term logs agent-1 --lines 500 --json                   # Last 500 lines of scrollback
rpi-term logs agent-1 --pane 1 --json                      # Specific pane
```

### poll — Wait for pattern in output

```bash
rpi-term poll agent-1 --until "BUILD SUCCESS" --json                   # Wait for pattern
rpi-term poll agent-1 --until "ready" --timeout 60 --json              # With timeout
rpi-term poll agent-1 --until "error|success" --interval 2.0 --json   # Custom interval
```

Pattern is a regex. Returns matched text and full pane content.

### fanout — Parallel execution

```bash
rpi-term fanout "npm test" --targets agent-1,agent-2,agent-3 --json         # Same command, multiple sessions
rpi-term fanout "git pull" --targets a1,a2,a3 --timeout 30 --json           # With timeout
```

Runs command in all target sessions concurrently using ThreadPoolExecutor. Returns ordered results.

## Key Patterns

- **Create sessions first** — `rpi-term session create` before running commands
- **Use `run` for commands that complete** — It waits and gives you exit code + output
- **Use `send` for interactive tools** — vim, ipython, anything that doesn't "finish"
- **Use `poll` to wait for async events** — Watch for build completion, server startup, etc.
- **Use `logs` to inspect** — Check what happened in a pane
- **Use `fanout` for parallel work** — Run same command across multiple sessions
- **Use `proc` for process management** — List, kill, and inspect processes instead of raw ps/kill
- **Use `--json` always** — Structured output for reliable parsing
- **Write all files to /tmp** — Any JSON, logs, or other files you generate must go to `/tmp/`. Never write output files into the project directory.

### proc — Process management

List, kill, inspect, and monitor processes. The agent's replacement for htop/top.

```bash
rpi-term proc list --json                                    # All user processes
rpi-term proc list --name python --json                      # Filter by name
rpi-term proc list --session job-abc123 --json               # Processes in a tmux session
rpi-term proc list --parent 12345 --json                     # Children of a PID
rpi-term proc list --cwd /path/to/project --json             # Processes running from a directory
rpi-term proc kill 12345 --json                              # Kill by PID (SIGTERM → wait → SIGKILL)
rpi-term proc kill --name "python" --json                    # Kill all matching name
rpi-term proc kill 12345 --tree --json                       # Kill PID and all children
rpi-term proc kill 12345 --force --json                       # Force kill (SIGKILL, no grace period)
rpi-term proc kill 12345 --signal 9 --json                   # Same as --force
rpi-term proc tree 12345 --json                              # Show process tree from PID
rpi-term proc top --session job-abc123 --json                # Resource snapshot for session
rpi-term proc top --pid 12345,12346 --json                   # Resource snapshot for specific PIDs
```

Each process includes `cwd` (working directory) in its JSON output — use this to identify processes spawned from a specific project or directory.

**Kill uses a two-step pattern**: sends the signal (default SIGTERM), waits up to 5 seconds for graceful exit, then SIGKILL if still alive. Use `--tree` to kill a process and all its children (critical for Python subprocesses).

#### Process cleanup pattern

During cleanup, `cd` back to your original working directory and use `proc list` to find processes you started that you don't need running anymore. If the task specified they should keep running, leave them alone.

```bash
1. rpi-term proc list --session job-abc123 --json   → see what's running
2. rpi-term proc kill <pid> --tree --json           → kill it and children
3. rpi-term proc list --name <name> --json          → verify nothing survived
```

## Sentinel Protocol

rpi-term wraps commands with markers: `echo "__START_<token>" ; <cmd> ; echo "__DONE_<token>:?$?"`

This gives:
- Reliable completion detection (no guessing)
- Accurate exit code capture
- Clean output extraction (only content between markers)

## Key Differences from macOS Drive

- **Linux-specific tools** - Uses Linux ps/pgrep instead of macOS Activity Monitor
- **tmux** - Same as macOS, but session management may differ
- **Process signals** - SIGTERM/SIGKILL work the same, but process tree handling is Linux-specific
- **Working directory** - Uses /proc filesystem for cwd detection

## Rules

- **Always use `--json`** — Structured output for reliable parsing
- **Write all files to /tmp** — Never write output files into the project directory
- **Create sessions before running commands** — Don't try to run commands in non-existent sessions
- **Use `run` for completion**, `send` for interactive tools
- **Run `rpi-term help <cmd>`** if you're unsure about a command's flags
