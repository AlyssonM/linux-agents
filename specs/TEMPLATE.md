# Task title

## Instructions
- As you work, keep track of your notes in a text editor or markdown file.
- If you work longer than 10 minutes from your start time, wrap up the current phase and record partial results.
- Do not skip environment notes. Record whether the test is running on X11 or Wayland, the host model, and any missing dependencies.
- For X11 scenarios, record whether a display manager service is active (`display-manager`, `lightdm`, `gdm`, or `sddm`) and which one is used on the host.
- Save command output and artifacts under a dated run directory such as `artifacts/e2e/YYYYMMDD-HHMM/`.

## Tasks
- [ ] First note the current date and time, host name, desktop session type, and operator name.
- [ ] Confirm `DISPLAY` value and capture display-manager status for the current desktop session.
- [ ] List the exact commands that will be used for the test run.
- [ ] Record any prerequisites that are missing before execution starts.
- [ ] Execute the workflow step by step and capture artifacts after each major step.
- [ ] Mark each step as pass, fail, or skip with a short reason.
- [ ] Summarize final status, issues, and follow-up actions.

## Deliverables
- A short report containing:
  - environment summary
  - commands executed
  - pass/fail/skip status per step
  - links or paths to screenshots, logs, OCR output, and server/client artifacts
  - known issues, limitations, and recommended fixes
