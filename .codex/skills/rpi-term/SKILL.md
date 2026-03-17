---
name: rpi-term
description: Terminal automation CLI for AI agents. Use rpi-term to create tmux sessions, execute commands, send keystrokes, read output, poll for patterns, run commands in parallel across sessions, and manage processes. Always use --json for structured output.
---

# rpi-term — Terminal Automation via tmux

Run from: `cd linux-agents/apps/rpi-term && rpi-term <command>`

rpi-term gives you full programmatic control over tmux sessions — creating terminals, running commands, reading output, and orchestrating parallel workloads.

## Commands

### session — Manage tmux sessions

```bash
rpi-term session create --name agent-1 --json                     # Opens a tmux session (headed)
rpi-term session create --name agent-1 --window build --json      # Named window
rpi-term session list --json                                      # List all sessions
rpi-term session kill --name agent-1 --json                       # Kill a session
rpi-term session attach --name agent-1 --json                     # Attach to session in lxterminal (VNC)
```

**Note**: `--name` is required for create/kill/attach.

### run — Execute command and wait for completion

Uses sentinel protocol (`__DONE_<token>:<exit_code>`) for reliable completion detection.

```bash
rpi-term run "npm test" --session agent-1 --json                     # Run and wait
rpi-term run "make build" --session agent-1 --timeout 120 --json     # Custom timeout
rpi-term run "ls" --session agent-1 --pane 1 --json                  # Target specific pane
```

Returns: exit code, captured output between sentinels.

### send — Raw keystrokes (no completion waiting)

For interactive tools (vim, ipython, etc.) where sentinel detection would interfere.

```bash
rpi-term send "vim file.txt" --session agent-1 --json                # Send command
rpi-term send ":wq" --session agent-1 --json                         # Send vim command
rpi-term send "y" --session agent-1 --no-enter --json                # Send without Enter
```

### logs — Capture pane output

```bash
rpi-term logs --session agent-1 --json                               # Current pane content
rpi-term logs --session agent-1 --lines 500 --json                   # Last 500 lines of scrollback
rpi-term logs --session agent-1 --pane 1 --json                      # Specific pane
```

### poll — Wait for pattern in output

```bash
rpi-term poll --session agent-1 --until "BUILD SUCCESS" --json                   # Wait for pattern
rpi-term poll --session agent-1 --until "ready" --timeout 60 --json              # With timeout
rpi-term poll --session agent-1 --until "error|success" --interval 2.0 --json   # Custom interval
```

Pattern is a regex. Returns matched text and full pane content.

### fanout — Parallel execution

```bash
rpi-term fanout "npm test" --sessions agent-1,agent-2,agent-3 --json         # Same command, multiple sessions
rpi-term fanout "git pull" --sessions a1,a2,a3 --timeout 30 --json           # With timeout
```

Runs command in all target sessions concurrently. Returns ordered results.

## Key Patterns

- **Create sessions first** — `rpi-term session create --name <name>` before running commands.
- **Use `run` for commands that complete** — It waits and gives you exit code + output.
- **Use `send` for interactive tools** — vim, ipython, anything that doesn't "finish".
- **Use `poll` to wait for async events** — Watch for build completion, server startup, etc.
- **Use `logs` to inspect** — Check what happened in a pane.
- **Use `fanout` for parallel work** — Run same command across multiple sessions.
- **Use `proc` for process management** — List processes.
- **Use `--json` always** — Structured output for reliable parsing.
- **Write all files to /tmp** — Any JSON, logs, or other files you generate must go to `/tmp/`. Never write output files into the project directory.

### proc — Process management

```bash
rpi-term proc list --json                                    # All user processes
rpi-term proc list --name python --json                      # Filter by name
```

## Sentinel Protocol

rpi-term wraps commands with markers: `echo "__START_<token>" ; <cmd> ; echo "__DONE_<token>:?$?"`

This gives:
- Reliable completion detection (no guessing)
- Accurate exit code capture
- Clean output extraction (only content between markers)

## Rules

- **Always use `--json`** — Structured output for reliable parsing.
- **Write all files to /tmp** — Never write output files into the project directory.
- **Create sessions before running commands** — Don't try to run commands in non-existent sessions.
- **Use `run` for completion**, `send` for interactive tools.
- **Run `rpi-term help <cmd>`** if you're unsure about a command's flags.
