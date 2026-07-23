"""Atomic file write: write-to-tmp then rename."""
from __future__ import annotations

from pathlib import Path


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write content to path atomically (write-to-tmp then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding=encoding)
    tmp.replace(path)  # POSIX: atomic rename(2); Windows: MoveFileEx
