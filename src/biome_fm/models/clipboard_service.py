"""Qt-free clipboard for file cut/copy/paste operations."""
from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClipboardEntry:
    paths: tuple[Path, ...]
    is_cut: bool


class ClipboardService:
    """In-memory clipboard for file paths; no Qt dependency."""

    _HISTORY_MAX = 20

    def __init__(self) -> None:
        self._paths: list[Path] = []
        self._is_cut: bool = False
        self._history: deque[ClipboardEntry] = deque(maxlen=self._HISTORY_MAX)

    def cut(self, paths: Iterable[Path]) -> None:
        self._paths = list(paths)
        self._is_cut = True
        self._history.append(ClipboardEntry(tuple(self._paths), True))

    def copy(self, paths: Iterable[Path]) -> None:
        self._paths = list(paths)
        self._is_cut = False
        self._history.append(ClipboardEntry(tuple(self._paths), False))

    def history(self) -> list[ClipboardEntry]:
        """Most-recent-first."""
        return list(reversed(self._history))

    def restore_history(self, entry: ClipboardEntry) -> None:
        self._paths = list(entry.paths)
        self._is_cut = entry.is_cut

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
