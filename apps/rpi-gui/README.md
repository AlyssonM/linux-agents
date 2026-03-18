# rpi-gui

GUI automation CLI for Linux ARM64 (Raspberry Pi), including screenshot capture, OCR, and desktop input control.

## Core Commands

- `rpi-gui see` captures screenshots with optional OCR metadata
- `rpi-gui ocr` extracts text from the current screen using Tesseract
- `rpi-gui click` clicks by coordinates or matched text
- `rpi-gui type` types text in the focused window
- `rpi-gui hotkey`, `scroll`, `drag` perform advanced input actions
- `rpi-gui apps`, `screens`, `window`, `find` inspect and control desktop context

## Requirements

Install system dependencies:

```bash
sudo apt install tesseract-ocr tesseract-ocr-eng scrot xdotool wmctrl
```

## Setup

```bash
uv venv
uv sync --extra dev
uv run rpi-gui --help
```

## Usage

```bash
uv run rpi-gui see --ocr
uv run rpi-gui ocr --output artifacts/ocr.json
uv run rpi-gui click --x 100 --y 200
uv run rpi-gui click --text "Submit"
uv run rpi-gui type "Hello world" --enter
```

## Testing

```bash
uv run pytest -q
```
