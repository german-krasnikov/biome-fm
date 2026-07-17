"""Qt-free clipboard for file cut/copy/paste operations."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class ClipboardService:
    """In-memory clipboard for file paths; no Qt dependency."""

    def __init__(self) -> None:
        self._paths: list[Path] = []
        self._is_cut: bool = False

    def cut(self, paths: Iterable[Path]) -> None:
        self._paths = list(paths)
        self._is_cut = True

    def copy(self, paths: Iterable[Path]) -> None:
        self._paths = list(paths)
        self._is_cut = False

    def paste(self, dest: Path) -> tuple[list[Path], bool]:
        """Return (paths, is_cut). Cut paste auto-clears; copy paste does not."""
        if not self._paths:
            return [], False
        paths, is_cut = list(self._paths), self._is_cut
        if is_cut:
            self.clear()
        return paths, is_cut

    def clear(self) -> None:
        self._paths = []
        self._is_cut = False

    @property
    def has_cut(self) -> set[Path]:
        """Paths currently staged for cut (empty if copy or empty)."""
        return set(self._paths) if self._is_cut else set()
