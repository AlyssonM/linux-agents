from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image


def _capture_with_grim(output_path: str) -> bool:
    """Capture screenshot using grim (Wayland native). Returns True if successful."""
    grim = shutil.which("grim")
    if not grim:
        return False
    
    try:
        subprocess.run(
            [grim, output_path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _capture_with_scrot(output_path: str) -> bool:
    """Capture screenshot using scrot (X11). Returns True if successful."""
    scrot = shutil.which("scrot")
    if not scrot:
        return False
    
    try:
        subprocess.run(
            [scrot, output_path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def capture_screenshot_to_file(output_path: str | None = None) -> Path:
    """
    Capture screenshot using best available tool.
    
    Priority:
    1. grim (Wayland native, most reliable in Wayland sessions)
    2. scrot (X11 tool, works via Xwayland in some cases)
    3. Fallback: will return Path to external capture if tools fail
    
    Args:
        output_path: Optional output path. If None, generates timestamped path.
        
    Returns:
        Path to captured screenshot.
        
    Raises:
        RuntimeError: If no screenshot tool is available.
    """
    if output_path is None:
        output_path = str(
            Path("artifacts") / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        )
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Try grim first (Wayland native - best for Wayland/Xwayland)
    if _capture_with_grim(str(output)):
        return output
    
    # Try scrot as fallback (X11 tool)
    if _capture_with_scrot(str(output)):
        return output
    
    raise RuntimeError(
        "No screenshot tool available. Install grim (Wayland) or scrot (X11):\n"
        "  sudo apt install grim # Wayland\n"
        "  sudo apt install scrot # X11"
    )


def capture_screenshot() -> Image.Image:
    """
    Capture screenshot using Python libraries (PIL/pyautogui).
    
    Note: This may not work reliably in Wayland sessions.
    Prefer capture_screenshot_to_file() for Wayland compatibility.
    
    Returns:
        PIL Image object.
        
    Raises:
        RuntimeError: If unable to capture screenshot.
    """
    try:
        from PIL import ImageGrab

        return ImageGrab.grab()  # type: ignore[attr-defined]
    except Exception:
        try:
            import pyautogui

            return pyautogui.screenshot()
        except Exception as exc:
            raise RuntimeError(
                "Unable to capture screenshot using Python libraries. "
                "Use capture_screenshot_to_file() for better Wayland support."
            ) from exc


def save_screenshot(image: Image.Image, output_path: str | None = None) -> Path:
    """
    Save a PIL Image to file.
    
    Args:
        image: PIL Image to save.
        output_path: Optional output path. If None, generates timestamped path.
        
    Returns:
        Path to saved image.
    """
    output = (
        Path(output_path)
        if output_path
        else Path("artifacts") / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output
