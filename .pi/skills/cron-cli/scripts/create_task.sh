#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "usage: create_task.sh <name> <schedule> <instruction> <script_file>"
  exit 1
fi

name="$1"
schedule="$2"
instruction="$3"
script_file="$4"

cd /home/alyssonpi/.openclaw/workspace/linux-agents/apps/cron-cli
uv run cron-cli create \
  --name "$name" \
  --schedule "$schedule" \
  --instruction "$instruction" \
  --script-file "$script_file" \
  --json
