"""Stdlib-only IPC client — no Qt dependency."""
from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path


def _socket_path() -> Path:
    if sys.platform == "win32":
        raise NotImplementedError("IPC client not supported on Windows")
    return Path(tempfile.gettempdir()) / "biome-fm"


def send_command(payload: dict, timeout: float = 2.0) -> None:
    path = _socket_path()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(str(path))
        sock.sendall(json.dumps(payload).encode())
