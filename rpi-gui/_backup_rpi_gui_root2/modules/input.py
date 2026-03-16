from __future__ import annotations

import shutil
import subprocess
from typing import Iterable

import pyautogui


class InputError(RuntimeError):
    """Raised when simulated input action fails."""


def run_hotkey(keys: Iterable[str]) -> None:
    sequence = [normalize_key(k) for k in keys if k and k.strip()]
    if not sequence:
        raise InputError("No valid keys provided")
    try:
        pyautogui.hotkey(*sequence)
    except Exception as exc:
        raise InputError(f"Hotkey failed: {exc}") from exc


def run_scroll(direction: str, steps: int, clicks_per_step: int = 120) -> int:
    if steps <= 0:
        raise InputError("steps must be greater than zero")
    direction = direction.lower().strip()
    if direction not in {"up", "down"}:
        raise InputError("direction must be 'up' or 'down'")

    amount = steps * clicks_per_step
    if direction == "down":
        amount = -amount

    try:
        pyautogui.scroll(amount)
    except Exception as exc:
        raise InputError(f"Scroll failed: {exc}") from exc
    return amount


def run_drag(from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.2, button: str = "left") -> None:
    if duration < 0:
        raise InputError("duration must be >= 0")
    if button not in {"left", "middle", "right"}:
        raise InputError("button must be one of: left, middle, right")

    try:
        pyautogui.moveTo(from_x, from_y)
        pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
    except Exception as exc:
        raise InputError(f"Drag failed: {exc}") from exc


def focus_window(query: str, *, exact: bool = False) -> str:
    if not query or not query.strip():
        raise InputError("window query cannot be empty")

    xdotool = shutil.which("xdotool")
    if not xdotool:
        raise InputError("xdotool not found in PATH")

    pattern = f"^{query}$" if exact else query
    search = subprocess.run([xdotool, "search", "--name", pattern], capture_output=True, text=True)
    if search.returncode != 0 or not search.stdout.strip():
        detail = search.stderr.strip() or "no matching windows"
        raise InputError(f"Unable to find window: {detail}")

    window_id = search.stdout.strip().splitlines()[0].strip()
    activate = subprocess.run([xdotool, "windowactivate", "--sync", window_id], capture_output=True, text=True)
    if activate.returncode != 0:
        detail = activate.stderr.strip() or "windowactivate failed"
        raise InputError(f"Failed to focus window {window_id}: {detail}")

    return window_id


def click_at(x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0) -> None:
    if x < 0 or y < 0:
        raise ValueError("Coordinates must be non-negative.")
    if button not in {"left", "middle", "right"}:
        raise InputError("button must be one of: left, middle, right")
    try:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
    except Exception as exc:
        raise InputError(f"Click failed: {exc}") from exc


def type_text(text: str, interval: float = 0.0, press_enter: bool = False) -> None:
    if text is None:
        raise ValueError("Text must not be None.")
    try:
        pyautogui.write(text, interval=interval)
        if press_enter:
            pyautogui.press("enter")
    except Exception as exc:
        raise InputError(f"Type failed: {exc}") from exc


def normalize_key(key: str) -> str:
    key = key.strip().lower()
    aliases = {
        "ctrl": "ctrl",
        "control": "ctrl",
        "cmd": "command",
        "win": "win",
        "super": "win",
        "option": "alt",
        "return": "enter",
        "esc": "escape",
    }
    return aliases.get(key, key)
