# GUI Workflow on Linux Desktop

## Instructions
- As you work, keep track of your notes in a text editor or markdown file.
- If you work longer than 10 minutes from your start time, wrap up and report the current state.
- Use a Linux GUI application that is available on the target machine. Prefer `gedit`; if unavailable, use `mousepad`, `leafpad`, `libreoffice`, or `firefox`.
- Save all screenshots and OCR output for later review.

## Requirements
- Active desktop session with visible application windows
- Screenshot support working in the current session
- OCR dependencies installed
- Input injection permitted by the compositor/window system

## Tasks
- [ ] Open a GUI application with a text field or editable document.
- [ ] If using a browser, navigate to a simple page with visible text and an obvious clickable element.
- [ ] Run `rpi-gui see --ocr` and save the JSON output.
- [ ] Verify that the screenshot file exists and is readable.
- [ ] Inspect the OCR output and identify a visible word or UI label that can be targeted.
- [ ] Run `rpi-gui click` using either safe coordinates or `--text` targeting a visible label.
- [ ] Run `rpi-gui type "hello from rpi-gui e2e" --enter`.
- [ ] Run `rpi-gui see --ocr` again to capture the post-action state.
- [ ] Verify that the resulting screenshot or OCR output shows the typed text, changed focus, or expected UI transition.
- [ ] Record whether the workflow was fully automated or required manual assistance.

## Expected Outputs
- Initial screenshot JSON with `screenshot`, dimensions, OCR text, and OCR elements
- Successful click JSON showing coordinates and button
- Successful type JSON showing character count
- Final screenshot or OCR evidence showing the intended result

## Deliverables
- A report containing:
  - application used
  - initial OCR findings
  - click target chosen
  - typed text
  - verification evidence from the final screenshot/OCR pass
  - pass/fail/skip result for each step
  - notes on compositor or application-specific quirks

## Known Issues / Limitations
- OCR text matching may fail for icon-only controls or low-contrast themes.
- Wayland may prevent synthetic input or window focus changes depending on desktop environment.
- Browser UI labels vary by locale and theme, so text-targeted clicks should use visible labels captured in the same session.
- On slower Raspberry Pi systems, application startup and OCR may need extra wait time.
