"""Tests for extended OpQueue."""
import threading
import time

from biome_fm.commands.base import Command
from biome_fm.operations.queue import OpQueue
from biome_fm.operations.task import Cancelled, OpProgress


class _SlowCmd(Command):
    def execute(self):
        time.sleep(0.05)

    def undo(self): ...


class _CancelCmd(Command):
    def __init__(self, cancel):
        self._cancel = cancel

    def execute(self):
        if self._cancel.is_set():
            raise Cancelled()

    def undo(self): ...


def _drain_until(q, predicate, timeout=2.0):
    events = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        events.extend(q.drain())
        if predicate(events):
            return events
        time.sleep(0.01)
    return events


def test_submit_with_task_id():
    q = OpQueue(max_workers=1)
    task = q.submit(_SlowCmd(), task_id=99)
    assert task.task_id == 99
    q.shutdown()


def test_cancel_produces_cancelled_event():
    q = OpQueue(max_workers=1)
    cancel = threading.Event()
    cancel.set()
    q.submit(_CancelCmd(cancel), cancel=cancel, task_id=1)
    events = _drain_until(q, lambda evts: any(type(e).__name__ == "OpCancelled" for e in evts))
    types = [type(e).__name__ for e in events]
    assert "OpCancelled" in types
    q.shutdown()


def test_next_task_id():
    q = OpQueue()
    a = q.next_task_id()
    b = q.next_task_id()
    assert b > a
    q.shutdown()


def test_put_event():
    q = OpQueue()
    q.put_event(OpProgress(1, 0, 1, 50, 100, "test.txt"))
    events = q.drain()
    assert len(events) == 1
    q.shutdown()
