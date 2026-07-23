"""Shared formatting utilities."""
from __future__ import annotations


def format_size(size: int) -> str:
    """Return human-readable file size: '1.4 MB', '320 B', etc."""
    s = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024:
            return f"{s:.0f} {unit}" if unit == "B" else f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} PB"
