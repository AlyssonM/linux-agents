#!/usr/bin/env python3
import sys
import subprocess

instruction = '''Say SUCCESS and stop'''

# Call OpenClaw agent with the instruction
cmd = [
    "/usr/bin/node",
    "/home/alyssonpi/.npm-global/lib/node_modules/openclaw/openclaw.mjs",
    "agent",
    "--agent", "main",
    "--message", instruction,
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

if result.returncode == 0:
    print(result.stdout)
    sys.exit(0)
else:
    print(f"Error: {result.stderr}", file=sys.stderr)
    sys.exit(result.returncode)
