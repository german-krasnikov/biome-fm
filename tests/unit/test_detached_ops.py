"""F268 — Detached Batch Operations: OpQueue.active_count()."""
import threading

import pytest

from biome_fm.commands.base import Command
from biome_fm.operations.queue import OpQueue


class _SlowCmd(Command):
    """Blocks until release event is set."""

    def __init__(self, started: threading.Event, release: threading.Event) -> None:
        self._started = started
        self._release = release

    def execute(self) -> None:
        self._started.set()
        self._release.wait(timeout=5)

    def undo(self) -> None:
        pass


def test_active_count_zero_when_idle() -> None:
    q = OpQueue()
    assert q.active_count() == 0
    q.shutdown()


def test_active_count_tracks_running() -> None:
    q = OpQueue()
    started = threading.Event()
    release = threading.Event()

    q.submit(_SlowCmd(started, release))
    assert started.wait(timeout=2), "task never started"
    assert q.active_count() > 0

    release.set()
    q.shutdown(wait=True)
    assert q.active_count() == 0
