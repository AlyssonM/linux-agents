from __future__ import annotations

import shutil
import subprocess
from typing import Iterable


def click_at(x: int, y: int, button: str = "left", clicks: int = 1, interval: float = 0.0) -> None:
    if x < 0 or y < 0:
        raise ValueError("Coordinates must be non-negative.")

    try:
        import pyautogui

        pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval)
    except Exception as exc:
        raise RuntimeError("Failed to perform click input.") from exc


def type_text(text: str, interval: float = 0.0, press_enter: bool = False) -> None:
    if text is None:
        raise ValueError("Text must not be None.")

    try:
        import pyautogui

        pyautogui.write(text, interval=interval)
        if press_enter:
            pyautogui.press("enter")
    except Exception as exc:
        raise RuntimeError("Failed to type text input.") from exc


def run_hotkey(keys: Iterable[str]) -> None:
    sequence = [normalize_key(k) for k in keys if k and k.strip()]
    if not sequence:
        raise ValueError("No valid keys provided")

    try:
        import pyautogui

        pyautogui.hotkey(*sequence)
    except Exception as exc:
        raise RuntimeError("Failed to send hotkey.") from exc


def run_scroll(direction: str, steps: int, clicks_per_step: int = 120) -> int:
    if steps <= 0:
        raise ValueError("steps must be greater than zero")

    d = direction.lower().strip()
    if d not in {"up", "down"}:
        raise ValueError("direction must be 'up' or 'down'")

    amount = steps * clicks_per_step
    if d == "down":
        amount = -amount

    try:
        import pyautogui

        pyautogui.scroll(amount)
    except Exception as exc:
        raise RuntimeError("Failed to scroll.") from exc
    return amount


def run_drag(
    from_x: int,
    from_y: int,
    to_x: int,
    to_y: int,
    duration: float = 0.2,
    button: str = "left",
) -> None:
    if duration < 0:
        raise ValueError("duration must be >= 0")
    if button not in {"left", "middle", "right"}:
        raise ValueError("button must be one of: left, middle, right")

    try:
        import pyautogui

        pyautogui.moveTo(from_x, from_y)
        pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
    except Exception as exc:
        raise RuntimeError("Failed to drag.") from exc


def focus_window(query: str, *, exact: bool = False) -> str:
    if not query or not query.strip():
        raise ValueError("window query cannot be empty")

    xdotool = shutil.which("xdotool")
    if not xdotool:
        raise RuntimeError("xdotool not found in PATH")

    pattern = f"^{query}$" if exact else query

    search = subprocess.run(
        [xdotool, "search", "--name", pattern],
        capture_output=True,
        text=True,
    )
    if search.returncode != 0 or not search.stdout.strip():
        detail = search.stderr.strip() or "no matching windows"
        raise RuntimeError(f"Unable to find window: {detail}")

    window_id = search.stdout.strip().splitlines()[0].strip()

    activate = subprocess.run(
        [xdotool, "windowactivate", "--sync", window_id],
        capture_output=True,
        text=True,
    )
    if activate.returncode != 0:
        detail = activate.stderr.strip() or "windowactivate failed"
        raise RuntimeError(f"Failed to focus window {window_id}: {detail}")

    return window_id


def normalize_key(key: str) -> str:
    key = key.strip().lower()
    aliases = {
        "ctrl": "ctrl",
        "control": "ctrl",
        "cmd": "command",
        "super": "win",
        "option": "alt",
        "return": "enter",
        "esc": "escape",
    }
    return aliases.get(key, key)
