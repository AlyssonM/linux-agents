"""
LocalSend integration module for rpi-gui - fixed version.

Uses LocalSend client API correctly.
"""

import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class LocalSendError(Exception):
    """Base exception for LocalSend errors."""
    pass


def discover_devices(timeout: float = 5.0) -> List[dict]:
    """
    Discover LocalSend devices.

    Args:
        timeout: Discovery timeout in seconds

    Returns:
        List of device dicts
    """
    # Importar do módulo localsend existente
    skills_path = Path.home() / ".openclaw/workspace/skills/localsend"
    if str(skills_path) not in sys.path:
        sys.path.insert(0, str(skills_path))

    from scripts.discovery import discover_devices as ls_discover

    devices = ls_discover(timeout=timeout)

    return list(devices)  # Retornar LocalSendDevice objects diretamente


def send_files_to_device(file_paths: List[str], target_device) -> dict:
    """
    Send files to device using LocalSend client.

    Args:
        file_paths: List of file paths to send
        target_device: LocalSendDevice object

    Returns:
        Result dict
    """
    # Importar cliente LocalSend
    skills_path = Path.home() / ".openclaw/workspace/skills/localsend"
    if str(skills_path) not in sys.path:
        sys.path.insert(0, str(skills_path))

    from scripts.client import LocalSendClient

    # Criar cliente
    client = LocalSendClient()

    # Enviar arquivos
    success = client.send_files(
        target=target_device,
        files=file_paths,
        verify_ssl=False,
    )

    return {
        "success": success,
        "device": target_device.alias,
        "host": target_device.ip,
        "files_sent": len(file_paths) if success else 0,
        "files_total": len(file_paths),
    }


def discover_and_send(file_paths: List[str], target_name: str = None) -> dict:
    """
    Discover devices and send files to target.

    Args:
        file_paths: List of file paths to send
        target_name: Optional device name filter

    Returns:
        Result dict
    """
    # Descobrir dispositivos
    devices = discover_devices(timeout=5.0)

    if not devices:
        raise LocalSendError("No LocalSend devices found on network")

    # Filtrar por nome se especificado
    if target_name:
        matched = [d for d in devices if target_name.lower() in d.alias.lower()]
        if not matched:
            available = ", ".join(d.alias for d in devices)
            raise LocalSendError(
                f"No device matching '{target_name}' found. Available: {available}"
            )
        target = matched[0]
    else:
        target = devices[0]

    # Enviar arquivos
    return send_files_to_device(file_paths, target)
