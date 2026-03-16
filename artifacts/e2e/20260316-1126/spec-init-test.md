# Linux ARM64 Agent Stack Initialization Test

## Instructions
- Follow this plan top-to-bottom. Stop and report on any blocking failure.
- This is a proof-of-work integration test for real Raspberry Pi hardware; do not silently assume GUI access exists.
- Keep notes in a text file during execution, including timestamps, command output snippets, and artifact paths.
- Prefer running from the repository root: `/home/alyssonpi/.openclaw/workspace/linux-agents`.

## Requirements

### Hardware
- Raspberry Pi 4 or comparable Linux ARM64 machine
- Connected monitor and active desktop session
- Keyboard and mouse input available

### Software
- Python 3.11+
- `tmux`
- `tesseract-ocr` and `tesseract-ocr-eng`
- `scrot`
- `xdotool`
- `wmctrl`
- Desktop application available for typing test (`gedit`, `mousepad`, `leafpad`, `libreoffice`, or equivalent)

## Tasks

### PHASE 1: SETUP
- [ ] `cd /home/alyssonpi/.openclaw/workspace/linux-agents`
- [ ] Verify Python and pip versions.
- [ ] Verify desktop session information: `echo "$XDG_SESSION_TYPE"`, `echo "$DISPLAY"`, and `echo "$WAYLAND_DISPLAY"`.
- [ ] Verify required system packages are present: `tmux`, `tesseract`, `scrot`, `xdotool`, `wmctrl`.
- [ ] Create or activate a virtual environment.
- [ ] Install editable packages for all four components:
  - `pip install -e rpi-gui[dev] -e rpi-term[dev] -e rpi-job[dev] -e rpi-client[dev]`
- [ ] Record any missing dependency or environment mismatch.

Expected:
- Python environment is active.
- All dependencies install without fatal errors.
- Desktop session type is known and documented.

### PHASE 2: BUILD
- [ ] From `rpi-gui`, run a package build or install verification (`python -m build` or editable import check).
- [ ] From `rpi-term`, run a package build or install verification.
- [ ] From `rpi-job`, run a package build or install verification.
- [ ] From `rpi-client`, run a package build or install verification.
- [ ] Verify CLIs respond to `--help`:
  - `rpi-gui --help`
  - `rpi-term --help`
  - `python -m rpi_job.main --help` or `uvicorn rpi_job.main:app --help`
  - `rpi-client --help`

Expected:
- All four components import/build successfully.
- CLI help output is available.
- No component fails due to packaging or entry-point issues.

### PHASE 3: PERMISSIONS
- [ ] Confirm screenshot capture works in the current desktop session.
- [ ] Confirm OCR can access captured screenshots.
- [ ] Confirm input injection is permitted in the current desktop session.
- [ ] Confirm window enumeration or focus control works where supported.
- [ ] Confirm `tmux` can create sessions for the current user.
- [ ] Document whether the environment is X11, Wayland, VNC, or headless.

Expected:
- GUI commands either work or fail with a clearly documented environment limitation.
- `tmux` works for the current user.

Notes:
- On Wayland, `xdotool` and some focus/window operations may be partially or fully blocked.
- On headless systems, GUI phases may be skipped but must be explicitly marked as skipped, not passed.

### PHASE 4: TEST INDIVIDUAL COMMANDS

#### 4.1 rpi-gui see
- [ ] Run `rpi-gui see`.
- [ ] Verify JSON output contains `screenshot`, `width`, and `height`.
- [ ] Verify the screenshot file exists on disk.

#### 4.2 rpi-gui see --ocr
- [ ] Run `rpi-gui see --ocr`.
- [ ] Verify JSON output contains OCR text and element coordinates.

#### 4.3 rpi-gui click
- [ ] Run `rpi-gui click --x <safe_x> --y <safe_y>` using a harmless desktop location.
- [ ] Verify command returns success JSON.

#### 4.4 rpi-gui type
- [ ] Open a text-capable GUI app.
- [ ] Run `rpi-gui type "hello from linux arm64 init test" --enter`.
- [ ] Verify text appears in the target app.

#### 4.5 rpi-term session lifecycle
- [ ] Run `rpi-term session create --name init-e2e`.
- [ ] Run `rpi-term session list` and verify `init-e2e` appears.
- [ ] Run `rpi-term run --session init-e2e "echo READY && uname -a"`.
- [ ] Run `rpi-term logs --session init-e2e --lines 50`.
- [ ] Run `rpi-term poll --session init-e2e --until "READY"`.
- [ ] Run `rpi-term session kill --name init-e2e`.

#### 4.6 rpi-job API
- [ ] Start the job server on port `7600`.
- [ ] Submit a job with `curl` or equivalent to `POST /job`.
- [ ] Fetch the job via `GET /job/{id}`.
- [ ] List jobs via `GET /jobs`.
- [ ] Stop a job via `DELETE /job/{id}`.

#### 4.7 rpi-client HTTP communication
- [ ] Run `rpi-client start http://127.0.0.1:7600 "collect system info"`.
- [ ] Run `rpi-client list http://127.0.0.1:7600`.
- [ ] Run `rpi-client latest http://127.0.0.1:7600 -n 1`.
- [ ] Run `rpi-client get http://127.0.0.1:7600 <job_id>`.
- [ ] Run `rpi-client stop http://127.0.0.1:7600 <job_id>` if still running.

Expected:
- Basic smoke coverage for GUI, terminal, API, and client paths.
- Each command yields either a valid success result or a documented environment-related skip/failure.

### PHASE 5: INTEGRATION TEST
- [ ] Start `rpi-job` server.
- [ ] Create a `tmux` session named `integration-e2e`.
- [ ] Use `rpi-term run` to produce visible terminal output, such as `echo terminal-ok`.
- [ ] Open a GUI text application.
- [ ] Run `rpi-gui see --ocr` and save the screenshot/OCR artifact.
- [ ] Use `rpi-gui click` to focus the GUI application or a visible text field.
- [ ] Run `rpi-gui type "integration workflow complete" --enter`.
- [ ] Submit a job with `rpi-client start http://127.0.0.1:7600 "integration test job"`.
- [ ] Poll the job until it reaches a terminal state using `rpi-client get`.
- [ ] Capture final evidence with:
  - terminal logs
  - GUI screenshot
  - job YAML output
  - client output

Expected:
- End-to-end proof that GUI automation, terminal automation, and HTTP job orchestration can coexist in one workflow.

### PHASE 6: REPORT
- [ ] Summarize setup status and dependency readiness.
- [ ] Summarize build/import status for all four components.
- [ ] Summarize permission findings for GUI and tmux access.
- [ ] Mark each Phase 4 command test as pass/fail/skip.
- [ ] Mark the Phase 5 integration workflow as pass/fail/skip.
- [ ] Record issues, crashes, slow paths, and Raspberry Pi-specific bottlenecks.
- [ ] Record recommended fixes for packaging, docs, environment detection, or command ergonomics.

## Deliverables
- A report containing:
  - environment summary
  - setup and dependency status
  - build status for `rpi-gui`, `rpi-term`, `rpi-job`, and `rpi-client`
  - pass/fail/skip matrix for all command tests
  - integration workflow result
  - paths to screenshots, OCR JSON, terminal logs, and job artifacts
  - recommended fixes and next actions

## Known Issues / Limitations
- Wayland may block or degrade `xdotool`-based click, type, focus, and window interactions.
- OCR quality depends on display scaling, font size, theme contrast, and screenshot method.
- Raspberry Pi hardware may require longer waits for application launch and OCR completion.
- Headless sessions without a desktop must skip GUI validation explicitly.
- If no Linux text editor is installed, substitute another visible text-input application and note the change.
