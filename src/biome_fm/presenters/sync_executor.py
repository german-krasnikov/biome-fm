"""SyncExecutor — VFS-agnostic sync operation runner."""
from __future__ import annotations

import threading
from collections.abc import Callable

from biome_fm.presenters.sync_presenter import SyncOp


class SyncExecutor:
    def __init__(
        self,
        vfs,
        cancel: threading.Event,
        progress: Callable[[int, int, str], None] | None = None,
    ) -> None:
        self._vfs = vfs
        self._cancel = cancel
        self._progress = progress

    def execute(self, ops: list[SyncOp]) -> int:
        total = len(ops)
        done = 0
        for op in ops:
            if self._cancel.is_set():
                break
            if op.action == "delete_orphan":
                self._vfs.delete(op.src)
            else:
                self._vfs.copy(op.src, op.dst)
            done += 1
            if self._progress:
                self._progress(done, total, op.src.name)
        return done
