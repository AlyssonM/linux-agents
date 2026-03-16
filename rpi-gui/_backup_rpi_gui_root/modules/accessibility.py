from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import subprocess
from typing import Any


@dataclass(slots=True)
class AccessibleElement:
    name: str
    role: str
    app: str
    states: list[str]
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "app": self.app,
            "states": self.states,
            "description": self.description,
        }


class AccessibilityError(RuntimeError):
    pass


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def _load_pyatspi() -> Any:
    try:
        import pyatspi  # type: ignore

        return pyatspi
    except Exception:
        return None


def _iter_descendants(node: Any) -> list[Any]:
    stack = [node]
    out: list[Any] = []
    while stack:
        current = stack.pop()
        out.append(current)
        try:
            for i in range(current.childCount):
                child = current.getChildAtIndex(i)
                if child is not None:
                    stack.append(child)
        except Exception:
            continue
    return out


def list_running_apps() -> list[dict[str, Any]]:
    if not _has_display():
        raise AccessibilityError("No GUI display detected (DISPLAY/WAYLAND_DISPLAY missing)")

    pyatspi = _load_pyatspi()
    if pyatspi is not None:
        desktop = pyatspi.Registry.getDesktop(0)
        apps: list[dict[str, Any]] = []
        for i in range(desktop.childCount):
            app = desktop.getChildAtIndex(i)
            try:
                name = app.name or "<unnamed>"
                role = app.getRoleName()
            except Exception:
                name = "<unknown>"
                role = "application"

            apps.append({"name": name, "role": role})

        dedup: dict[str, dict[str, Any]] = {}
        for app in apps:
            dedup[app["name"]] = app
        return sorted(dedup.values(), key=lambda a: a["name"].lower())

    proc = _run(["wmctrl", "-lp"])
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise AccessibilityError(
            "AT-SPI unavailable and wmctrl fallback failed" + (f": {stderr}" if stderr else "")
        )

    apps: dict[str, dict[str, Any]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        wm_class_title = parts[4]
        candidate = wm_class_title.split()[-1] if wm_class_title else "unknown"
        apps[candidate] = {"name": candidate, "role": "application"}
    return sorted(apps.values(), key=lambda a: a["name"].lower())


def find_elements(
    text: str | None = None,
    role: str | None = None,
    app: str | None = None,
    exact: bool = False,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    if max_results < 1:
        raise AccessibilityError("max_results must be >= 1")
    if not _has_display():
        raise AccessibilityError("No GUI display detected (DISPLAY/WAYLAND_DISPLAY missing)")

    pyatspi = _load_pyatspi()
    if pyatspi is None:
        raise AccessibilityError("pyatspi is not available; install AT-SPI Python bindings")

    desktop = pyatspi.Registry.getDesktop(0)
    results: list[dict[str, Any]] = []

    text_norm = text if exact else (text.lower() if text else None)
    role_norm = role.lower() if role else None
    app_norm = app.lower() if app else None

    for i in range(desktop.childCount):
        app_node = desktop.getChildAtIndex(i)
        app_name = (getattr(app_node, "name", "") or "").strip() or "<unnamed>"

        if app_norm and app_norm not in app_name.lower():
            continue

        for node in _iter_descendants(app_node):
            try:
                node_name = (getattr(node, "name", "") or "").strip()
                node_role = node.getRoleName()
                state_set = node.getState()
                states = [str(s) for s in state_set.getStates()] if state_set else []
                desc = getattr(node, "description", None)
            except Exception:
                continue

            if text_norm is not None:
                if exact:
                    if node_name != text:
                        continue
                elif text_norm not in node_name.lower():
                    continue

            if role_norm and role_norm not in node_role.lower():
                continue

            results.append(
                AccessibleElement(
                    name=node_name,
                    role=node_role,
                    app=app_name,
                    states=states,
                    description=desc,
                ).to_dict()
            )
            if len(results) >= max_results:
                return results

    return results


def list_screens() -> list[dict[str, Any]]:
    if not _has_display():
        raise AccessibilityError("No GUI display detected (DISPLAY/WAYLAND_DISPLAY missing)")

    proc = _run(["xrandr", "--query"])
    screens: list[dict[str, Any]] = []

    if proc.returncode == 0:
        pattern = re.compile(r"^(?P<name>\S+) connected(?: primary)? (?P<w>\d+)x(?P<h>\d+)\+(?P<x>\d+)\+(?P<y>\d+)")
        idx = 0
        for line in proc.stdout.splitlines():
            m = pattern.match(line.strip())
            if not m:
                continue
            screens.append({
                "index": idx,
                "name": m.group("name"),
                "x": int(m.group("x")),
                "y": int(m.group("y")),
                "width": int(m.group("w")),
                "height": int(m.group("h")),
            })
            idx += 1

    if screens:
        return screens

    try:
        from PIL import ImageGrab

        img = ImageGrab.grab()
        return [{"index": 0, "name": "primary", "x": 0, "y": 0, "width": img.width, "height": img.height}]
    except Exception as exc:
        raise AccessibilityError("Unable to enumerate screens (xrandr/Pillow failed)") from exc


def list_windows() -> list[dict[str, Any]]:
    proc = _run(["wmctrl", "-lGpx"])
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise AccessibilityError("Unable to list windows via wmctrl" + (f": {stderr}" if stderr else ""))

    windows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = line.split(None, 8)
        if len(parts) < 9:
            continue
        windows.append({
            "id": parts[0],
            "desktop": parts[1],
            "x": int(parts[2]),
            "y": int(parts[3]),
            "width": int(parts[4]),
            "height": int(parts[5]),
            "host": parts[6],
            "wm_class": parts[7],
            "title": parts[8],
        })
    return windows


def _resolve_window_id(target: str) -> str:
    target_lower = target.lower()
    for w in list_windows():
        if w["id"].lower() == target_lower or target_lower in w["title"].lower() or target_lower in w["wm_class"].lower():
            return w["id"]
    raise AccessibilityError(f"Window not found for target: {target}")


def move_window(target: str, x: int, y: int, width: int | None = None, height: int | None = None) -> dict[str, Any]:
    win_id = _resolve_window_id(target)
    w = width if width is not None else -1
    h = height if height is not None else -1
    proc = _run(["wmctrl", "-ir", win_id, "-e", f"0,{x},{y},{w},{h}"])
    if proc.returncode != 0:
        raise AccessibilityError((proc.stderr or "Failed to move window").strip())
    return {"ok": True, "action": "move", "id": win_id, "x": x, "y": y, "width": w, "height": h}


def resize_window(target: str, width: int, height: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
    win_id = _resolve_window_id(target)
    rx = x if x is not None else -1
    ry = y if y is not None else -1
    proc = _run(["wmctrl", "-ir", win_id, "-e", f"0,{rx},{ry},{width},{height}"])
    if proc.returncode != 0:
        raise AccessibilityError((proc.stderr or "Failed to resize window").strip())
    return {"ok": True, "action": "resize", "id": win_id, "x": rx, "y": ry, "width": width, "height": height}


def minimize_window(target: str) -> dict[str, Any]:
    win_id = _resolve_window_id(target)
    proc = _run(["wmctrl", "-ir", win_id, "-b", "add,hidden"])
    if proc.returncode != 0:
        raise AccessibilityError((proc.stderr or "Failed to minimize window").strip())
    return {"ok": True, "action": "minimize", "id": win_id}


def maximize_window(target: str) -> dict[str, Any]:
    win_id = _resolve_window_id(target)
    proc = _run(["wmctrl", "-ir", win_id, "-b", "add,maximized_vert,maximized_horz"])
    if proc.returncode != 0:
        raise AccessibilityError((proc.stderr or "Failed to maximize window").strip())
    return {"ok": True, "action": "maximize", "id": win_id}


def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)
