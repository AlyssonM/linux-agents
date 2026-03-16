# Terminal and GUI Integration

## Instructions
- As you work, keep track of your notes in a text editor or markdown file.
- If you work longer than 10 minutes from your start time, wrap up and report what completed.
- This workflow validates that `rpi-term` and `rpi-gui` can operate against the same desktop session in a realistic operator flow.

## Requirements
- `tmux` installed and functional
- Terminal emulator available on the desktop (`lxterminal`, `gnome-terminal`, `xfce4-terminal`, `xterm`, or equivalent)
- `rpi-gui` input and screenshot commands operational in the current session

## Tasks
- [ ] Open a visible terminal emulator window on the desktop.
- [ ] Create a tmux session: `rpi-term session create --name gui-term-e2e`.
- [ ] Run a command in the session: `rpi-term run --session gui-term-e2e "echo READY && pwd && uname -a"`.
- [ ] Capture session output with `rpi-term logs --session gui-term-e2e --lines 100`.
- [ ] Run `rpi-term poll --session gui-term-e2e --until "READY"`.
- [ ] Use `rpi-gui see --ocr` to capture the visible terminal window.
- [ ] If the terminal window is not focused, use `rpi-gui click` on the terminal region or title area.
- [ ] Use `rpi-gui type "echo GUI_INPUT_OK" --enter` to inject visible terminal input.
- [ ] Capture output again with `rpi-term logs --session gui-term-e2e --lines 100`.
- [ ] Verify both layers of evidence:
  - tmux output contains `READY`
  - tmux output contains `GUI_INPUT_OK`
  - GUI screenshot shows the terminal window and corresponding text where possible
- [ ] Kill the session: `rpi-term session kill --name gui-term-e2e`.

## Expected Outputs
- Successful session creation output
- `run` output containing `READY`, `pwd`, and `uname -a`
- `logs` output showing command history
- `poll` success when `READY` appears
- GUI screenshot with the terminal visible
- Evidence that GUI typing affected the terminal window or, if not, a documented failure mode

## Deliverables
- A report containing:
  - terminal emulator used
  - tmux session name
  - command output before and after GUI interaction
  - screenshot and OCR artifact paths
  - whether GUI input reached the intended terminal window
  - pass/fail/skip result for every step

## Known Issues / Limitations
- A tmux session can exist without being attached to the visible terminal window; if attachment is manual, record the exact step used.
- GUI typing may target the wrong window if focus is unstable or OCR targeting is inaccurate.
- Wayland can restrict synthetic input or focus transfer.
- Fast terminal redraw and small fonts can reduce OCR usefulness.
