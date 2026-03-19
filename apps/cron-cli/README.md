# cron-cli

CLI for CRUD management of cron tasks backed by shell scripts and operational instructions.

## What it does

- Creates tasks with `name`, `instruction`, `schedule`, and an executable script
- Stores metadata in `~/.local/share/cron-cli/tasks/*.json`
- Stores scripts in `~/.local/share/cron-cli/scripts/*.sh`
- Maintains a managed block in your `crontab -e`

## Setup

```bash
cd /home/alyssonpi/.openclaw/workspace/linux-agents/apps/cron-cli
uv sync --extra dev
uv run cron-cli --help
```

## Commands

- `create` creates a task
- `list` lists tasks
- `get` retrieves a task by id
- `update` updates a task
- `delete` removes a task
- `apply` rebuilds the managed crontab block
- `run` executes the task script immediately

## Examples

```bash
uv run cron-cli create \
  --name healthcheck \
  --instruction "Check internal endpoint and record failures" \
  --schedule "*/5 * * * *" \
  --script 'curl -fsS http://127.0.0.1:8080/health || echo "healthcheck failed"'
```

```bash
uv run cron-cli list --json
uv run cron-cli get <task_id> --json
```

```bash
uv run cron-cli update <task_id> --schedule "0 * * * *" --instruction "Run every hour"
uv run cron-cli run <task_id> --json
uv run cron-cli delete <task_id>
```

## Testing

```bash
uv run pytest -q
```
