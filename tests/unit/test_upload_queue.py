"""Tests for OpQueue event drain."""
from __future__ import annotations

import time

from biome_fm.commands.base import Command
from biome_fm.operations.queue import OpQueue


class TestOpQueue:
    def test_progress_callback_fires(self):
        """OpQueue submit → OpStarted + OpDone events appear in drain."""
        from biome_fm.operations.task import OpDone, OpStarted

        class NoopCmd(Command):
            def execute(self) -> None:
                pass

            def undo(self) -> None:
                pass

        q = OpQueue(max_workers=1)
        q.submit(NoopCmd())
        time.sleep(0.1)
        events = q.drain()
        types = [type(e).__name__ for e in events]
        assert "OpStarted" in types
        assert "OpDone" in types
        q.shutdown()
