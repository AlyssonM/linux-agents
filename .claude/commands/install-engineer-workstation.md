---
model: opus
description: Install and verify the engineer's workstation for sending jobs to the linux-agents sandbox
argument-hint: [sandbox-ip-or-hostname]
---

# Purpose

Set up the engineer's workstation (Linux, macOS, or Windows with WSL) to send jobs to the remote linux-agents sandbox on Raspberry Pi. Installs minimal dependencies, configures the sandbox URL, verifies connectivity, and confirms the full client-to-server pipeline works end-to-end.

## Variables

SANDBOX_HOST: $ARGUMENTS
RPI_JOB_PORT: 7600

## Instructions

- All commands run locally on the engineer's workstation — this is the PRIMARY device, not the sandbox
- This device only needs the CLI client tools — it does NOT need rpi-gui, rpi-term, or the full server stack
- If a dependency is already installed, skip it and note the version
- If a step fails, stop and report the failure — do not continue blindly
- Use appropriate package manager for your OS (apt, brew, chocolatey, etc.)
- Use `uv` for Python dependency management if available, otherwise use `pip`
- If SANDBOX_HOST is not provided, ask the user for the Raspberry Pi's IP or hostname
- Do NOT modify the sandbox device — only configure this local workstation
- SSH connectivity is optional but recommended for debugging

## Workflow

### Phase 1: Install

1. Check OS and architecture:
   ```bash
   uname -s -m
   ```

2. Check Python version:
   ```bash
   python3 --version
   ```
   Must be 3.11 or higher for compatibility with the sandbox.

3. Check what's already installed:
   ```bash
   which python3 pip uv git ssh curl
   ```
   Then for each found tool, run its version command:
   - `python3 --version`
   - `pip --version`
   - `uv --version` (if installed)
   - `git --version`
   - `ssh -V`

4. Install uv (Python package manager) if missing - faster than pip:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc  # or log out and back in
   ```

5. Install missing tools based on OS:

   **Linux (Debian/Ubuntu):**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git curl
   ```

   **macOS:**
   ```bash
   brew install python3 git curl
   ```

   **Windows (WSL):**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git curl
   ```

### Phase 2: Clone and Setup Repository

6. Verify the repo exists. Clone if needed:
   ```bash
   git clone https://github.com/AlyssonM/linux-agents.git ~/linux-agents
   cd ~/linux-agents
   ```

   If repo already exists, `cd` to it and pull latest:
   ```bash
   cd ~/linux-agents
   git pull origin main
   ```

7. Install rpi-client dependencies:
   ```bash
   cd rpi-client
   uv sync
   # OR if uv is not available:
   pip install -e .
   cd ..
   ```

8. If SANDBOX_HOST is not provided, ask the user:
   ```
   Please provide the Raspberry Pi's IP address or hostname (e.g., 192.168.1.100 or rpi.local):
   ```

   Once provided, set the environment variable:
   ```bash
   export SANDBOX_HOST="192.168.1.100"  # or whatever the user provided
   ```

9. Test network connectivity to the sandbox:
   ```bash
   ping -c 3 $SANDBOX_HOST
   ```
   Expected: Successful ping responses
   **Result:** PASS/FAIL

10. Optional: Test SSH connectivity (useful for debugging):
    ```bash
    ssh -o ConnectTimeout=5 $SANDBOX_HOST "echo SSH connection successful"
    ```
    Expected: "SSH connection successful" (or prompt for password if SSH keys not set up)
    **Result:** PASS/FAIL

### Phase 3: Verify

Run each check and record PASS/FAIL. Do not stop on failure — run all checks and report results at the end.

11. **rpi-client CLI** — verify the client parses correctly:
    ```bash
    cd rpi-client
    uv run python -m rpi_client --help
    ```
    Expected: Output showing all commands (start, status, list, stop, clear, logs)
    **Result:** PASS/FAIL

12. **Server connectivity** — verify rpi-job server is reachable:
    ```bash
    curl -s http://$SANDBOX_HOST:$RPI_JOB_PORT/health || echo "Health endpoint not available (may be OK)"
    ```
    Expected: HTTP response (may be 404 if /health not implemented, but server is responding)
    **Result:** PASS/FAIL

13. **Job submission** — submit a simple test job:
    ```bash
    JOB_ID=$(uv run python -m rpi_client start http://$SANDBOX_HOST:$RPI_JOB_PORT "echo Hello from workstation" --json | grep -o '"job_id": "[^"]*"' | cut -d'"' -f4)
    echo "Job ID: $JOB_ID"
    ```
    Expected: 8-character job ID (e.g., "a3f7b2c1")
    **Result:** PASS/FAIL

14. **Job polling** — wait for job to complete:
    ```bash
    sleep 3
    STATUS=$(uv run python -m rpi_client status http://$SANDBOX_HOST:$RPI_JOB_PORT $JOB_ID --json | grep -o '"status": "[^"]*"' | cut -d'"' -f4)
    echo "Job status: $STATUS"
    ```
    Expected: Status is "done"
    **Result:** PASS/FAIL

15. **Result retrieval** — get job output:
    ```bash
    SUMMARY=$(uv run python -m rpi_client status http://$SANDBOX_HOST:$RPI_JOB_PORT $JOB_ID --json | grep -o '"summary": "[^"]*"' | cut -d'"' -f4)
    echo "Job summary: $SUMMARY"
    ```
    Expected: Summary contains "Hello from workstation"
    **Result:** PASS/FAIL

16. **Job listing** — verify we can list all jobs:
    ```bash
    uv run python -m rpi_client list http://$SANDBOX_HOST:$RPI_JOB_PORT --json
    ```
    Expected: JSON output with jobs array containing our test job
    **Result:** PASS/FAIL

### Phase 4: Configuration (Optional)

17. Set up environment variables for convenience:

    Create `~/.config/rpi-client/config.sh` (or add to `~/.bashrc`):
    ```bash
    export RPI_JOB_URL="http://$SANDBOX_HOST:$RPI_JOB_PORT"
    ```

    Source it:
    ```bash
    source ~/.config/rpi-client/config.sh
    ```

    Now you can use the short form:
    ```bash
    rpi-client start "ls -la"  # Uses $RPI_JOB_URL by default
    ```

    **Result:** PASS/FAIL (configuration created)

### Final Summary

Report all verification results in a table:

| Check | Status | Notes |
|-------|--------|-------|
| Python 3.11+ | PASS/FAIL | Version: |
| Git installed | PASS/FAIL | |
| Network connectivity | PASS/FAIL | |
| SSH connectivity (optional) | PASS/FAIL | |
| rpi-client CLI | PASS/FAIL | |
| Server reachable | PASS/FAIL | |
| Job submission | PASS/FAIL | Job ID: |
| Job completion | PASS/FAIL | Status: |
| Result retrieval | PASS/FAIL | Summary: |
| Job listing | PASS/FAIL | |
| Environment configured | PASS/FAIL | |

If all core checks PASS (network, rpi-client, job submission, job completion), the workstation is ready to send jobs to the linux-agents sandbox! 🚀

## Usage Examples

Now that your workstation is configured, you can submit jobs to the sandbox:

**Simple command:**
```bash
rpi-client start "ls -la"
```

**Terminal automation:**
```bash
rpi-client start "rpi-term run test 'npm test'"
```

**GUI automation:**
```bash
rpi-client start "rpi-gui click --id B1"
```

**Check status:**
```bash
rpi-client status <job_id>
```

**List all jobs:**
```bash
rpi-client list
```

## Troubleshooting

**Network connectivity fails:**
- Verify Raspberry Pi is on: `ping $SANDBOX_HOST`
- Check firewall settings on Raspberry Pi
- Ensure rpi-job server is running on sandbox

**Job submission fails:**
- Verify rpi-job server is running: `ssh $SANDBOX_HOST "ps aux | grep rpi-job"`
- Check server logs: `ssh $SANDBOX_HOST "cat /tmp/rpi-job.log"`
- Verify port is not blocked by firewall

**Python version too old:**
- Install Python 3.11+ via pyenv, deadsnakes PPA, or official installer
- On macOS: `brew install python@3.11`
- On Ubuntu: `sudo apt install python3.11`

**uv command not found:**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Or use pip instead: `pip install -e ./rpi-client`

**SSH connection refused:**
- Enable SSH on Raspberry Pi: `sudo raspi-config` → Interface Options → SSH
- Verify hostname/IP is correct
- Check if username is needed: `username@$SANDBOX_HOST`

## Next Steps

Once your workstation is configured:

1. **Try the E2E tests:**
   ```bash
   cd ~/linux-agents/specs
   # Read and follow the test specifications
   ```

2. **Explore the skills:**
   ```bash
   cat .claude/skills/rpi-gui/SKILL.md
   cat .claude/skills/rpi-term/SKILL.md
   cat .claude/skills/rpi-job/SKILL.md
   ```

3. **Submit complex jobs:**
   - Combine rpi-gui and rpi-term in a single job
   - Use scripts for multi-step automation
   - Monitor job progress with `rpi-client status`

4. **Set up monitoring:**
   - Watch job logs in real-time
   - Set up alerts for job failures
   - Track resource usage on the sandbox

Happy automating! 🎉
