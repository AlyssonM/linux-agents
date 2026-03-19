#!/usr/bin/env bash
set -euo pipefail

cd /home/alyssonpi/.openclaw/workspace/linux-agents/apps/cron-cli
uv run cron-cli list --json
