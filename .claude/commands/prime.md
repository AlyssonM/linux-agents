---
description: Load foundational context about the linux-agents codebase — architecture, apps, skills, and key patterns
---

# Purpose

Understand the linux-agents monorepo: a Linux automation framework for Raspberry Pi with four tools (rpi-gui, rpi-term, rpi-job, rpi-client) that give AI agents full control of a Linux device via GUI and terminal automation.

## Workflow

1. Read project overview and structure:
   - READ `README.md`
   - READ `pyproject.toml` (root)

2. Read each tool's config:
   - READ `rpi-gui/pyproject.toml`
   - READ `rpi-term/pyproject.toml`
   - READ `rpi-job/pyproject.toml`
   - READ `rpi-client/pyproject.toml`

3. Read the agent skills and prompts:
   - READ `.claude/skills/rpi-gui/SKILL.md`
   - READ `.claude/skills/rpi-term/SKILL.md`
   - READ `.claude/skills/rpi-job/SKILL.md`
   - READ `.claude/skills/rpi-client/SKILL.md`
   - READ `.claude/agents/job-system-prompt.md`
   - READ `.claude/commands/rpi-gui-term-user-prompt.md`

4. Read entry points:
   - READ `rpi-gui/src/rpi_gui/__init__.py`
   - READ `rpi-term/src/rpi_term/main.py`
   - READ `rpi-job/src/rpi_job/main.py`
   - READ `rpi-client/src/rpi_client/main.py`

5. Read E2E test specs to understand usage patterns:
   - READ `specs/README.md`
   - READ `specs/TEMPLATE.md`
   - SCAN `specs/*.md` for test examples

6. Summarize: purpose, architecture (4 tools), stack (Python + pyatspi + xdotool + tmux + FastAPI), key patterns (observe-act-verify, sentinel protocol, job YAML tracking, element IDs), and how the pieces connect
