"""F234 — Thread-safe TTL cache for remote directory listings."""
from __future__ import annotations

import threading
import time
from pathlib import Path

from biome_fm.models.file_item import FileItem


class RemoteListCache:
    """Thread-safe TTL cache for remote directory listings."""

    def __init__(self, ttl: float = 30.0) -> None:
        self._ttl = ttl
        self._cache: dict[str, tuple[float, list[FileItem]]] = {}
        self._lock = threading.RLock()

    def get(self, path: Path) -> list[FileItem] | None:
        with self._lock:
            entry = self._cache.get(str(path))
            if entry and time.monotonic() - entry[0] < self._ttl:
                return list(entry[1])
        return None

    def set(self, path: Path, items: list[FileItem]) -> None:
        with self._lock:
            self._cache[str(path)] = (time.monotonic(), list(items))

    def invalidate(self, path: Path | None = None) -> None:
        with self._lock:
            if path is None:
                self._cache.clear()
            else:
                self._cache.pop(str(path), None)
