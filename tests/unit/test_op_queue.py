"""Unit tests for OpQueue — no Qt, pure threading."""

from __future__ import annotations

import threading
import time

from biome_fm.commands.base import Command
from biome_fm.operations.queue import OpQueue
from biome_fm.operations.task import OpDone, OpError, OpStarted


class FakeCommand(Command):
    def __init__(
        self, side_effect: Exception | None = None, gate: threading.Event | None = None,
    ) -> None:
        self.executed = False
        self._side_effect = side_effect
        self._gate = gate  # if set, block until gate is set before executing

    def execute(self) -> None:
        if self._gate:
            self._gate.wait()
        if self._side_effect:
            raise self._side_effect
        self.executed = True

    def undo(self) -> None:
        self.executed = False


def _drain_until(q: OpQueue, predicate, timeout: float = 2.0) -> list:
    """Drain events until predicate returns True or timeout."""
    events: list = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        events.extend(q.drain())
        if predicate(events):
            return events
        time.sleep(0.01)
    return events


def test_submit_executes_command() -> None:
    q = OpQueue()
    cmd = FakeCommand()
    q.submit(cmd)
    _drain_until(q, lambda evts: any(isinstance(e, OpDone) for e in evts))
    assert cmd.executed
    q.shutdown()


def test_drain_returns_started_and_done() -> None:
    q = OpQueue()
    cmd = FakeCommand()
    q.submit(cmd)
    events = _drain_until(q, lambda evts: any(isinstance(e, OpDone) for e in evts))
    types = [type(e) for e in events]
    assert OpStarted in types
    assert OpDone in types
    q.shutdown()


def test_drain_empty_when_no_tasks() -> None:
    q = OpQueue()
    assert q.drain() == []
    q.shutdown()


def test_error_produces_op_error_event() -> None:
    q = OpQueue()
    cmd = FakeCommand(side_effect=ValueError("boom"))
    q.submit(cmd)
    events = _drain_until(q, lambda evts: any(isinstance(e, OpError) for e in evts))
    errors = [e for e in events if isinstance(e, OpError)]
    assert len(errors) == 1
    assert isinstance(errors[0].error, ValueError)
    q.shutdown()


def test_error_does_not_crash_queue() -> None:
    q = OpQueue()
    q.submit(FakeCommand(side_effect=RuntimeError("first")))
    _drain_until(q, lambda evts: any(isinstance(e, OpError) for e in evts))
    cmd2 = FakeCommand()
    q.submit(cmd2)
    _drain_until(q, lambda evts: any(isinstance(e, OpDone) for e in evts))
    assert cmd2.executed
    q.shutdown()


def test_cancel_before_run_skips_execution() -> None:
    gate = threading.Event()
    q = OpQueue(max_workers=1)
    # first task hogs the single worker
    blocker = FakeCommand(gate=gate)
    q.submit(blocker)
    # second task — cancel it before worker picks it up
    cmd = FakeCommand()
    task = q.submit(cmd)
    q.cancel(task.task_id)
    gate.set()  # release blocker
    # wait for blocker to finish
    _drain_until(q, lambda evts: sum(1 for e in evts if isinstance(e, OpDone)) >= 1, timeout=3.0)
    # cmd should NOT have run — cancelled before execution
    assert not cmd.executed
    q.shutdown()


def test_shutdown_completes_in_flight() -> None:
    q = OpQueue()
    cmd = FakeCommand()
    q.submit(cmd)
    q.shutdown(wait=True)
    assert cmd.executed


def test_unique_task_ids() -> None:
    q = OpQueue()
    tasks = [q.submit(FakeCommand()) for _ in range(3)]
    ids = [t.task_id for t in tasks]
    assert len(set(ids)) == 3
    q.shutdown()
