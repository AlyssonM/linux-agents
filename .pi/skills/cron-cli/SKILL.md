---
name: cron-cli
description: CRUD management of cron tasks for agents. Create, list, inspect, update, and remove tasks with instructions and shell scripts that run regularly.
---

# cron-cli — Cron task CRUD with scripts

Run from: `cd /home/alyssonpi/.openclaw/workspace/linux-agents/apps/cron-cli && cron-cli <command>`

## Goal

`cron-cli` standardizes recurring tasks with:
- metadata (`name`, `instruction`, `schedule`)
- versioned shell scripts in local storage
- automatic sync to a managed `crontab` block

## Setup

```bash
cd /home/alyssonpi/.openclaw/workspace/linux-agents/apps/cron-cli
uv sync --extra dev
uv run cron-cli --help
```

## Commands

### create

```bash
cron-cli create \
  --name healthcheck \
  --instruction "Check internal endpoint" \
  --schedule "*/5 * * * *" \
  --script 'curl -fsS http://127.0.0.1:8080/health || echo "failure"'
```

```bash
cron-cli create \
  --name backup-db \
  --instruction "Daily database backup" \
  --schedule "0 2 * * *" \
  --script-file /tmp/backup_db.sh
```

### list / get

```bash
cron-cli list --json
cron-cli get <task_id> --json
```

### update

```bash
cron-cli update <task_id> \
  --schedule "0 * * * *" \
  --instruction "Run every hour"
```

### delete

```bash
cron-cli delete <task_id>
```

### apply

```bash
cron-cli apply
```

### run

```bash
cron-cli run <task_id> --json
```

## Helper scripts

```bash
~/.pi/skills/cron-cli/scripts/create_task.sh
~/.pi/skills/cron-cli/scripts/list_tasks.sh
```

## Rules

- Use `--json` for reliable agent parsing.
- Always provide `--instruction` with clear operational intent.
- Prefer `--script-file` for longer scripts.
- Run `cron-cli run <task_id>` before keeping a task enabled.
- Re-apply with `cron-cli apply` after manual crontab changes.
