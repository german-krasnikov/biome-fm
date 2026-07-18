"""Conflict resolution for file copy/move operations."""
from __future__ import annotations

import threading
from collections.abc import Callable
from enum import Enum, auto
from pathlib import Path


class ConflictAction(Enum):
    OVERWRITE = auto()
    OVERWRITE_ALL = auto()
    SKIP = auto()
    SKIP_ALL = auto()
    RENAME = auto()
    CANCEL = auto()
    ASK_EACH = auto()


def auto_rename(dst: Path) -> Path:
    """Return dst unchanged if it doesn't exist, else foo.txt → foo_1.txt → foo_2.txt."""
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    n = 1
    while True:
        candidate = dst.with_name(f"{stem}_{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


class ConflictResolver:
    """Thread-safe rendezvous: worker thread asks, main thread replies."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._event = threading.Event()
        self._action: ConflictAction | None = None
        self._apply_all: ConflictAction | None = None
        self._timeout = timeout
        self.on_conflict: Callable[[Path, Path, ConflictResolver], None] | None = None

    def ask(self, src: Path, dst: Path) -> ConflictAction:
        if self._apply_all is not None:
            return self._apply_all
        self._event.clear()
        self._action = None
        if self.on_conflict:
            self.on_conflict(src, dst, self)
        self._event.wait(timeout=self._timeout)
        return self._action if self._action is not None else ConflictAction.CANCEL

    def reply(self, action: ConflictAction) -> None:
        if action in (ConflictAction.OVERWRITE_ALL, ConflictAction.SKIP_ALL):
            self._apply_all = action
        self._action = action
        self._event.set()

    def reset(self) -> None:
        """Reset apply_all state for a new operation."""
        self._apply_all = None


class PreCopyConflictResolver:
    """Pre-decided conflict strategy — returns the same action for every conflict."""

    def __init__(self, action: ConflictAction, fallback: "ConflictResolver | None" = None) -> None:
        self._action = action
        self._fallback = fallback

    def ask(self, src: Path, dst: Path) -> ConflictAction:
        if self._action == ConflictAction.ASK_EACH:
            if self._fallback is not None:
                return self._fallback.ask(src, dst)
            return ConflictAction.CANCEL
        return self._action
