"""F286 — Operation Retry with exponential backoff tests."""
from __future__ import annotations

import threading
import time
from unittest.mock import patch

import pytest

from biome_fm.operations.task import OpDone, OpError


class _FailCmd:
    """Fails for the first `n_fails` executions, then succeeds."""

    def __init__(self, n_fails: int = 999) -> None:
        self.attempts = 0
        self.n_fails = n_fails

    def execute(self) -> None:
        self.attempts += 1
        if self.attempts <= self.n_fails:
            raise RuntimeError(f"fail #{self.attempts}")

    def undo(self) -> None:
        pass


def _wait_for_failed(q, task_id: int, timeout: float = 2.0) -> bool:
    """Poll until task_id appears in q._failed or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with q._lock:
            if task_id in q._failed:
                return True
        time.sleep(0.01)
    return False


def _drain_all(q, timeout: float = 2.0):
    """Drain events until OpDone or OpError seen, or timeout."""
    events = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        events.extend(q.drain())
        if any(isinstance(e, (OpDone, OpError)) for e in events):
            break
        time.sleep(0.01)
    return events


class TestOpRetry:
    def test_retry_resubmits_after_failure(self) -> None:
        """retry() re-runs the cmd; if it passes second time, OpDone is emitted."""
        from biome_fm.operations.queue import OpQueue

        q = OpQueue(max_workers=1)
        cmd = _FailCmd(n_fails=1)  # fails once, then succeeds
        task = q.submit(cmd)

        # wait for initial failure and drain initial events
        assert _wait_for_failed(q, task.task_id), "task should be in _failed"
        q.drain()  # consume OpStarted + OpError from first run

        # retry with max_retries=0 — cmd succeeds on second attempt
        q.retry(task.task_id, max_retries=0)

        events = _drain_all(q)
        assert any(isinstance(e, OpDone) and e.task_id == task.task_id for e in events)
        assert cmd.attempts == 2
        q.shutdown(wait=True)

    def test_max_retries_gives_up(self) -> None:
        """After max_retries exhausted the task ends up back in _failed."""
        import biome_fm.operations.queue as qmod
        from biome_fm.operations.queue import OpQueue

        q = OpQueue(max_workers=1)
        cmd = _FailCmd(n_fails=999)  # always fails
        task = q.submit(cmd)
        assert _wait_for_failed(q, task.task_id)

        # Patch Timer to fire immediately (no actual sleep)
        class ImmediateTimer:
            def __init__(self, delay, fn, args=None):
                self._fn = fn
                self._args = args or []

            def start(self) -> None:
                self._fn(*self._args)

        with patch.object(qmod.threading, "Timer", ImmediateTimer):
            q.retry(task.task_id, max_retries=2)
            # all retries fire synchronously via ImmediateTimer; wait for final failure
            assert _wait_for_failed(q, task.task_id), "task should be back in _failed"

        assert cmd.attempts == 4  # 1 original + 3 retried (max_retries=2 → 2 extra + 1 final)
        q.shutdown(wait=False)

    def test_exponential_backoff_delays(self) -> None:
        """Retry delays follow 2**attempt: 1, 2, 4 for max_retries=3."""
        import biome_fm.operations.queue as qmod
        from biome_fm.operations.queue import OpQueue

        q = OpQueue(max_workers=1)
        cmd = _FailCmd(n_fails=999)
        task = q.submit(cmd)
        assert _wait_for_failed(q, task.task_id)

        delays: list[float] = []

        class RecordTimer:
            def __init__(self, delay, fn, args=None):
                delays.append(delay)
                self._fn = fn
                self._args = args or []

            def start(self) -> None:
                self._fn(*self._args)

        with patch.object(qmod.threading, "Timer", RecordTimer):
            q.retry(task.task_id, max_retries=3)
            assert _wait_for_failed(q, task.task_id)

        assert delays == [1, 2, 4]
        q.shutdown(wait=False)
