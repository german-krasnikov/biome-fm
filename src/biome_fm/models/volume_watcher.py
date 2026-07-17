"""VolumeWatcher — polls for hot-plugged volumes and emits signals."""
from __future__ import annotations

import sys
from pathlib import Path

from biome_fm.qt import QObject, QTimer, Signal


def _list_volumes() -> set[Path]:
    if sys.platform == "darwin":
        try:
            return {p for p in Path("/Volumes").iterdir() if p.is_dir()}
        except OSError:
            return set()
    elif sys.platform == "linux":
        volumes: set[Path] = set()
        try:
            for line in Path("/proc/mounts").read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] not in ("/", ""):
                    volumes.add(Path(parts[1]))
        except OSError:
            pass
        return volumes
    else:  # Windows
        import string
        return {Path(f"{d}:\\") for d in string.ascii_uppercase if Path(f"{d}:\\").exists()}


class VolumeWatcher(QObject):
    volume_added = Signal(Path)
    volume_removed = Signal(Path)

    def __init__(self, interval_ms: int = 3000) -> None:
        super().__init__()
        self._interval_ms = interval_ms
        self._known: set[Path] = set()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def start(self) -> None:
        self._known = _list_volumes()
        self._timer.start(self._interval_ms)

    def _poll(self) -> None:
        current = _list_volumes()
        for p in current - self._known:
            self.volume_added.emit(p)
        for p in self._known - current:
            self.volume_removed.emit(p)
        self._known = current
