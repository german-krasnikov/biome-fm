"""Tests for upload queue / make_upload_queue (F304)."""
from __future__ import annotations

import threading
import time

from biome_fm.commands.base import Command
from biome_fm.operations.queue import OpQueue


class SleepCmd(Command):
    def __init__(self, duration: float, record: list) -> None:
        self._duration = duration
        self._record = record

    def execute(self) -> None:
        self._record.append(("start", time.monotonic()))
        time.sleep(self._duration)
        self._record.append(("end", time.monotonic()))

    def undo(self) -> None:
        pass


class TestUploadQueue:
    def test_serial_queue_single_worker(self):
        from biome_fm.operations.queue import make_upload_queue

        q = make_upload_queue()
        assert q._pool._max_workers == 1

    def test_progress_callback_fires(self):
        """OpQueue submit → OpStarted + OpDone events appear in drain."""
        from biome_fm.commands.base import Command
        from biome_fm.operations.task import OpDone, OpStarted

        class NoopCmd(Command):
            def execute(self) -> None:
                pass

            def undo(self) -> None:
                pass

        q = OpQueue(max_workers=1)
        task = q.submit(NoopCmd())
        # Give thread time to run
        time.sleep(0.1)
        events = q.drain()
        types = [type(e).__name__ for e in events]
        assert "OpStarted" in types
        assert "OpDone" in types
        q.shutdown()

    def test_ops_run_serially_with_single_worker(self):
        """Two ops submitted to a 1-worker queue must not overlap."""
        from biome_fm.operations.queue import make_upload_queue

        q = make_upload_queue()
        record: list = []
        q.submit(SleepCmd(0.05, record))
        q.submit(SleepCmd(0.05, record))
        time.sleep(0.2)
        q.shutdown()
        # With serial queue: end of first < start of second
        starts = [t for label, t in record if label == "start"]
        ends = [t for label, t in record if label == "end"]
        assert len(starts) == 2
        assert ends[0] <= starts[1] + 0.01  # tiny tolerance
