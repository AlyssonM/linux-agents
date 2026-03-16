# Codex Agent Structure for linux-agents

This directory mirrors the `.claude/` structure for Codex-oriented agent workflows inside `linux-agents`.

## Layout

```text
.codex/
├── agents/
├── commands/
├── skills/
└── STRUCTURE.md
```

## Purpose

- Reuse the same operational prompts, commands, and skills created for `.claude/`
- Keep a Codex-friendly location for future agent-specific customization
- Preserve parity between Claude-style and Codex-style project agent scaffolding

## Current State

This directory was replicated from `linux-agents/.claude/`.
At the moment, the contents are intentionally equivalent, with Linux/Raspberry Pi semantics:

- `rpi-gui` → GUI automation on Linux/X11
- `rpi-term` → tmux-based terminal automation
- `rpi-job` → FastAPI job server
- `rpi-client` → CLI job client

## Notes

- If Codex-specific instructions are needed later, they should be edited here instead of `.claude/`.
- Until then, `.claude/` and `.codex/` are kept logically aligned.
