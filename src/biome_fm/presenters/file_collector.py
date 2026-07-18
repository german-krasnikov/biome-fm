"""FileCollector — cherry-pick files from multiple dirs into a virtual panel."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.file_item import FileItem


class FileCollector:
    """Accumulates FileItems by path (deduplicated). Shows via navigate_virtual."""

    def __init__(self) -> None:
        self._items: dict[Path, FileItem] = {}

    def add(self, items: list[FileItem]) -> None:
        for item in items:
            self._items[item.path] = item

    def remove(self, paths: list[Path]) -> None:
        for p in paths:
            self._items.pop(p, None)

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> list[FileItem]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def show(self, pane) -> None:
        """Navigate pane to a virtual listing of collected files."""
        pane.navigate_virtual(self.items(), "Collected Files")
