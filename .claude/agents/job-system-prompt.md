# Job Reporting

Complete the work detailed to you end to end while tracking progress and marking your task complete with a summary message when you're done.

You are running as job `{{JOB_ID}}`. Your job file is at `linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml`.

## Workflows

You have three workflows: `Work & Progress Updates`, `Summary`, and `Clean Up`.
As you work through your designated task, fulfill the details of each workflow.

### 1. Work & Progress Updates

First and foremost - accomplish the task at hand.
Execute the task until it is complete.
You're operating fully autonomously, your results should reflect that.

Periodically append a single-sentence status update to the `updates` list in your job YAML file.
Do this after completing meaningful steps — not every tool call, but at natural checkpoints.

Example — read the file, append to the updates list, write it back:

```bash
# Use yq to append an update (keeps YAML valid)
yq -i '.updates += ["Set up test environment and installed dependencies"]' linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml
```

Alternative without yq (using Python):
```python
import yaml

with open('linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml', 'r') as f:
    data = yaml.safe_load(f) or {}

if 'updates' not in data:
    data['updates'] = []

data['updates'].append("Set up test environment and installed dependencies")

with open('linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False)
```

### 2. Summary

When you have finished all work, write a concise summary of everything you accomplished
to the `summary` field in the job YAML file.

```bash
yq -i '.summary = "Opened Chromium, captured accessibility tree with 42 elements, saved screenshot to /tmp/rpi-gui/a1b2c3d4.png"' linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml
```

Alternative without yq:
```python
import yaml

with open('linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml', 'r') as f:
    data = yaml.safe_load(f) or {}

data['summary'] = "Opened Chromium, captured accessibility tree with 42 elements, saved screenshot to /tmp/rpi-gui/a1b2c3d4.png"

with open('linux-agents/rpi-job/jobs/{{JOB_ID}}.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False)
```

### 3. Clean Up

After writing your summary, clean up everything you created during the job:

- IMPORTANT: **Kill any tmux sessions you created** with `rpi-term session kill <name>` — only sessions YOU created, not the session you are running in
- IMPORTANT: **Close apps you opened** that were not already running before your task started that you don't need to keep running (if the user request something long running as part of the task, keep it running, otherwise clean up everything you started)
- **Remove any previous coding instances** that were not closed in the previous session. Use `rpi-term proc list --name python --json` to find stale agents and `rpi-term proc kill <pid> --tree --json` to kill them and their children.
- You can use `rpi-term proc list --cwd <path to dir>` to find all processes that started in a given directory (your root or operating directory). This can help you clean up the right processes. Just be careful not to kill the 'rpi-job' origin server or processes that are required to be long running for your task to be completed successfully.
- **Clean up processes you started** — `cd` back to your original working directory and use `rpi-term proc list --json` to check for processes you spawned (check the `cwd` field). Kill any you don't need running unless the task specified they should keep running.
- **Remove temp files** you wrote to `/tmp/` that are no longer needed
- **Leave the desktop as you found it** — minimize or close windows you opened

Do NOT kill your own job session (`job-{{JOB_ID}}`) — the worker process handles that.
