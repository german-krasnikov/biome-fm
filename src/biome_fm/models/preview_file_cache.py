"""PreviewFileCache — local temp file cache for remote file preview (F305)."""
from __future__ import annotations

import hashlib
import threading
import time
from pathlib import Path


class PreviewFileCache:
    """Cache remote file bytes to local temp files, keyed by (path_str, mtime)."""

    def __init__(self, cache_dir: Path, max_mb: int = 50) -> None:
        self._dir = cache_dir
        self._max_bytes = max_mb * 1024 * 1024
        self._lock = threading.Lock()
        # Maps cache_key → (local_path, access_time)
        self._entries: dict[str, tuple[Path, float]] = {}

    def _key(self, path: Path, mtime: float) -> str:
        return hashlib.sha1(f"{path}:{mtime}".encode()).hexdigest()

    def get(self, path: Path, mtime: float) -> Path | None:
        key = self._key(path, mtime)
        with self._lock:
            entry = self._entries.get(key)
            if entry and entry[0].exists():
                self._entries[key] = (entry[0], time.monotonic())
                return entry[0]
            self._entries.pop(key, None)
        return None

    def put(self, path: Path, mtime: float, data: bytes) -> Path:
        key = self._key(path, mtime)
        local = self._dir / (key + path.suffix)
        local.write_bytes(data)
        with self._lock:
            self._entries[key] = (local, time.monotonic())
        return local

    def evict_lru(self) -> None:
        """Remove oldest entries until total size ≤ max_bytes."""
        with self._lock:
            ordered = sorted(self._entries.items(), key=lambda kv: kv[1][1])
            total = sum(p.stat().st_size for _, (p, _) in ordered if p.exists())
            for key, (local, _) in ordered:
                if total <= self._max_bytes:
                    break
                if local.exists():
                    total -= local.stat().st_size
                    local.unlink(missing_ok=True)
                del self._entries[key]
