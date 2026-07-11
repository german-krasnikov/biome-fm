"""OpTask and OpEvent types — no Qt imports."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from biome_fm.commands.base import Command


@dataclass(frozen=True)
class OpStarted:
    task_id: int


@dataclass(frozen=True)
class OpProgress:
    task_id: int
    done: int
    total: int


@dataclass(frozen=True)
class OpDone:
    task_id: int


@dataclass(frozen=True)
class OpError:
    task_id: int
    error: Exception


OpEvent = OpStarted | OpProgress | OpDone | OpError


@dataclass
class OpTask:
    task_id: int
    cmd: Command
    cancel: threading.Event = field(default_factory=threading.Event)
