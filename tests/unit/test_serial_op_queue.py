"""F207 — Serial Operation Queue tests."""
from __future__ import annotations

import time
import threading

import pytest


class _RecordCmd:
    def __init__(self, name: str, results: list[str], delay: float = 0.01) -> None:
        self.name = name
        self.results = results
        self.delay = delay

    def execute(self) -> None:
        time.sleep(self.delay)
        self.results.append(self.name)

    def undo(self) -> None:
        pass


class TestSerialOpQueue:
    def test_make_serial_queue_returns_single_worker(self) -> None:
        from biome_fm.operations.queue import make_serial_queue

        q = make_serial_queue()
        assert q._pool._max_workers == 1
        q.shutdown(wait=False)

    def test_ops_run_sequentially(self) -> None:
        from biome_fm.operations.queue import make_serial_queue

        q = make_serial_queue()
        results: list[str] = []
        q.submit(_RecordCmd("a", results))
        q.submit(_RecordCmd("b", results))
        q.shutdown(wait=True)
        assert results == ["a", "b"]
