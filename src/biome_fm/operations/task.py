"""OpTask and OpEvent types — no Qt imports."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from biome_fm.commands.base import Command


class Cancelled(Exception):
    """Raised inside a Command to signal user cancellation."""


@dataclass(frozen=True)
class OpStarted:
    task_id: int


@dataclass(frozen=True)
class OpProgress:
    task_id: int
    files_done: int
    files_total: int
    bytes_done: int
    bytes_total: int
    current_file: str


@dataclass(frozen=True)
class OpDone:
    task_id: int


@dataclass(frozen=True)
class OpError:
    task_id: int
    error: Exception


@dataclass(frozen=True)
class OpCancelled:
    task_id: int


@dataclass(frozen=True)
class OpConflict:
    task_id: int
    src: object  # Path
    dst: object  # Path
    resolver: object  # ConflictResolver — kept as object to avoid circular import


OpEvent = OpStarted | OpProgress | OpDone | OpError | OpCancelled | OpConflict


@dataclass
class OpTask:
    task_id: int
    cmd: Command
    cancel: threading.Event = field(default_factory=threading.Event)
