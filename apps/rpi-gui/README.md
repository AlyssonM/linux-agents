# rpi-gui

Core GUI automation CLI for Linux ARM64 (Raspberry Pi).

## Sprint 1 Commands

- `rpi-gui see` — capture screenshot, optional OCR metadata
- `rpi-gui ocr` — OCR from current screen (Tesseract)
- `rpi-gui click` — click by coordinates or OCR text
- `rpi-gui type` — type text into focused window

## Also integrated (Sprint 2/3 shared work)

- `hotkey`, `scroll`, `drag`, `focus`
- `apps list`, `screens list`, `window ...`, `find`

## Requirements

System packages:

```bash
sudo apt install tesseract-ocr tesseract-ocr-eng scrot xdotool wmctrl
```

## Install with uv

```bash
uv venv
uv sync --extra dev
uv run rpi-gui --help
```

## Example Usage

```bash
uv run rpi-gui see --ocr
uv run rpi-gui ocr --output artifacts/ocr.json
uv run rpi-gui click --x 100 --y 200
uv run rpi-gui click --text "Submit"
uv run rpi-gui type "Hello world" --enter
```

## Tests

```bash
uv run pytest -q
```

Test suite includes CLI and module-level coverage for all Sprint 1 operations and error paths.
