"""Temp-file panel logic — pure Python, no Qt."""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TempEntry:
    path: Path
    size: int
    age_days: float


def list_temp_entries(max_entries: int = 200) -> list[TempEntry]:
    """Scan the platform temp dir and return up to *max_entries* entries."""
    tmp = tempfile.gettempdir()
    now = time.time()
    entries: list[TempEntry] = []
    try:
        scan = list(os.scandir(tmp))
    except PermissionError:
        return []
    for entry in scan:
        if len(entries) >= max_entries:
            break
        try:
            stat = entry.stat()
            age = (now - stat.st_mtime) / 86400
            entries.append(TempEntry(Path(entry.path), stat.st_size, age))
        except PermissionError:
            continue
    return entries


def delete_entries(entries: list[TempEntry]) -> int:
    """Delete files/dirs in *entries*; return count successfully removed."""
    count = 0
    for e in entries:
        try:
            if e.path.is_dir():
                shutil.rmtree(e.path)
            else:
                e.path.unlink()
            count += 1
        except OSError:
            continue
    return count
