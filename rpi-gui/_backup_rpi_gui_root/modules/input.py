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
    except Exception as exc:  # pragma: no cover - defensive wrapper
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
    except Exception as exc:  # pragma: no cover
        raise InputError(f"Scroll failed: {exc}") from exc
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
        raise InputError("duration must be >= 0")
    if button not in {"left", "middle", "right"}:
        raise InputError("button must be one of: left, middle, right")

    try:
        pyautogui.moveTo(from_x, from_y)
        pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
    except Exception as exc:  # pragma: no cover
        raise InputError(f"Drag failed: {exc}") from exc


def focus_window(query: str, *, exact: bool = False) -> str:
    if not query or not query.strip():
        raise InputError("window query cannot be empty")

    xdotool = shutil.which("xdotool")
    if not xdotool:
        raise InputError("xdotool not found in PATH")

    base = [xdotool, "search"]
    if exact:
        base.append("--name")
        pattern = f"^{query}$"
    else:
        base.append("--name")
        pattern = query

    search = subprocess.run(
        [*base, pattern],
        capture_output=True,
        text=True,
    )

    if search.returncode != 0 or not search.stdout.strip():
        detail = search.stderr.strip() or "no matching windows"
        raise InputError(f"Unable to find window: {detail}")

    window_id = search.stdout.strip().splitlines()[0].strip()
    activate = subprocess.run(
        [xdotool, "windowactivate", "--sync", window_id],
        capture_output=True,
        text=True,
    )
    if activate.returncode != 0:
        detail = activate.stderr.strip() or "windowactivate failed"
        raise InputError(f"Failed to focus window {window_id}: {detail}")

    return window_id


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
