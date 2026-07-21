"""Qt-free space reclaimer presenter."""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from biome_fm.models.deps_scanner import scan_cleanup_dirs


@dataclass
class ReclaimEntry:
    path: Path
    size: int  # bytes


class SpaceReclaimerPresenter:
    def __init__(
        self,
        root: Path,
        patterns: frozenset[str],
        on_results: Callable[[list[ReclaimEntry]], None],
    ) -> None:
        self._root = root
        self._patterns = patterns
        self._on_results = on_results
        self._cancel = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._cancel.clear()
        self._thread = threading.Thread(target=self._scan, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        self._cancel.set()

    def _scan(self) -> None:
        dirs = scan_cleanup_dirs(self._root, self._cancel, patterns=self._patterns)
        if self._cancel.is_set():
            return
        entries = []
        for d in dirs:
            if self._cancel.is_set():
                return
            try:
                size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            except OSError:
                size = 0
            entries.append(ReclaimEntry(path=d, size=size))
        self._on_results(entries)
