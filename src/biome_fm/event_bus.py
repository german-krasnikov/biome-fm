"""Thread-safe publish/subscribe event bus. No Qt dependency."""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class EventBus:
    """Thread-safe, Qt-free publish/subscribe bus."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: dict[type, list[Callable[..., None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[..., None]) -> None:
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: type, handler: Callable[..., None]) -> None:
        import contextlib

        with self._lock:
            lst = self._handlers.get(event_type, [])
            with contextlib.suppress(ValueError):
                lst.remove(handler)

    def publish(self, event: Any) -> None:
        with self._lock:
            handlers = list(self._handlers.get(type(event), []))
        for h in handlers:
            h(event)


# Module-level singleton
bus = EventBus()


# ── Events ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FilesChanged:
    """A directory's contents changed — panes watching this path should refresh."""
    path: Path


@dataclass(frozen=True)
class ActivePaneChanged:
    """Which pane is now active (source)."""
    pane_id: str  # 'left' | 'right'


@dataclass(frozen=True)
class OperationStarted:
    """A file operation began."""
    description: str


@dataclass(frozen=True)
class OperationFinished:
    """A file operation completed."""
    description: str
    success: bool
    error: str = ""
