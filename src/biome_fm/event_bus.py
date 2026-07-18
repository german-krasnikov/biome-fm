"""Thread-safe publish/subscribe event bus. No Qt dependency."""
from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)


class EventBus:
    """Thread-safe, Qt-free publish/subscribe bus."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._handlers: dict[type, list[Callable[..., None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[..., None]) -> None:
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: type, handler: Callable[..., None]) -> None:
        with self._lock:
            lst = self._handlers.get(event_type, [])
            with contextlib.suppress(ValueError):
                lst.remove(handler)

    def publish(self, event: Any) -> None:
        with self._lock:
            handlers = list(self._handlers.get(type(event), []))
        for h in handlers:
            try:
                h(event)
            except Exception:
                _log.exception("EventBus handler %r raised for %r", h, event)


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


@dataclass(frozen=True)
class PaneNavigated:
    """Active pane navigated to a new path."""
    pane_id: str
    path: Path


@dataclass(frozen=True)
class SyncBrowsingToggled:
    """Sync browsing mode toggled."""
    enabled: bool


@dataclass(frozen=True)
class BookmarkChanged:
    """Bookmark list changed."""
    pass


@dataclass(frozen=True)
class ThemeChanged:
    """Theme was applied. Subscribers should re-polish dynamic properties."""
    name: str
    tokens: dict[str, str]


@dataclass(frozen=True)
class ShowHiddenToggled:
    """Show/hide dotfiles toggled."""
    enabled: bool


@dataclass(frozen=True)
class AsyncOpSubmitted:
    """An async file operation was submitted to OpQueue."""
    task_id: int
    description: str
    cancel: object  # threading.Event


@dataclass(frozen=True)
class RemoteConnected:
    """A remote connection was established."""
    scheme: str
    host: str


@dataclass(frozen=True)
class RemoteDisconnected:
    """A remote connection was closed."""
    scheme: str
    host: str


@dataclass(frozen=True)
class RemoteSyncing:
    """A remote I/O operation is in progress."""
    scheme: str
    host: str
    active: bool
