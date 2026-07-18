"""CrossDirMarks — aggregated marks across multiple directories. No Qt."""
from __future__ import annotations

from pathlib import Path


class CrossDirMarks:
    """Tracks marked paths keyed by directory, independent of per-pane marks."""

    def __init__(self) -> None:
        self._marks: dict[Path, set[Path]] = {}

    def add(self, directory: Path, path: Path) -> None:
        self._marks.setdefault(directory, set()).add(path)

    def remove(self, directory: Path, path: Path) -> None:
        if directory in self._marks:
            self._marks[directory].discard(path)

    def all_paths(self) -> list[Path]:
        return [p for paths in self._marks.values() for p in paths]

    def count(self) -> int:
        return sum(len(s) for s in self._marks.values())

    def clear(self) -> None:
        self._marks.clear()
