"""OpQueue — thread-pool backed command runner, zero Qt imports.

Drain pattern (caller side):
    timer = QTimer()
    timer.timeout.connect(lambda: [handle(e) for e in op_queue.drain()])
    timer.start(100)
"""

from __future__ import annotations

import itertools
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from biome_fm.commands.base import Command
from biome_fm.operations.task import (
    Cancelled,
    OpCancelled,
    OpDone,
    OpError,
    OpEvent,
    OpStarted,
    OpTask,
)

_id_gen = itertools.count(1)


def make_upload_queue() -> OpQueue:
    """Serial (single-worker) queue for remote uploads."""
    return OpQueue(max_workers=1)


def make_serial_queue() -> OpQueue:
    """Single-worker queue — ops run one at a time."""
    return OpQueue(max_workers=1)


class OpQueue:
    def __init__(self, max_workers: int = 2) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._events: queue.SimpleQueue[OpEvent] = queue.SimpleQueue()
        self._tasks: dict[int, OpTask] = {}
        self._failed: dict[int, OpTask] = {}
        self._lock = threading.Lock()

    def next_task_id(self) -> int:
        return next(_id_gen)

    def put_event(self, event: OpEvent) -> None:
        self._events.put(event)

    def submit(
        self,
        cmd: Command,
        cancel: threading.Event | None = None,
        task_id: int | None = None,
    ) -> OpTask:
        tid = task_id if task_id is not None else next(_id_gen)
        c = cancel or threading.Event()
        task = OpTask(task_id=tid, cmd=cmd, cancel=c)
        with self._lock:
            self._tasks[tid] = task
        self._pool.submit(self._run, task)
        return task

    def cancel(self, task_id: int) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
        if task:
            task.cancel.set()

    def retry(self, task_id: int, max_retries: int = 0) -> OpTask | None:
        """Re-submit a failed task. max_retries>0 uses exponential backoff (1s, 2s, 4s…)."""
        with self._lock:
            task = self._failed.pop(task_id, None)
        if task is None:
            return None
        if max_retries > 0:
            with self._lock:
                self._tasks[task_id] = task
            self._pool.submit(self._run, task, max_retries, 0)
            return task
        return self.submit(task.cmd, task.cancel, task_id=task_id)

    def skip(self, task_id: int) -> None:
        with self._lock:
            self._failed.pop(task_id, None)

    def active_count(self) -> int:
        """Return number of tasks currently running."""
        with self._lock:
            return len(self._tasks)

    def drain(self) -> list[OpEvent]:
        """Pull all pending events — call from main thread on QTimer."""
        events: list[OpEvent] = []
        try:
            while True:
                events.append(self._events.get_nowait())
        except queue.Empty:
            return events

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)

    def _run(self, task: OpTask, retries_left: int = 0, attempt: int = 0) -> None:
        if task.cancel.is_set():
            self._events.put(OpCancelled(task.task_id))
            with self._lock:
                self._tasks.pop(task.task_id, None)
            return
        if attempt == 0:
            self._events.put(OpStarted(task.task_id))
        _retry_scheduled = False
        try:
            task.cmd.execute()
            self._events.put(OpDone(task.task_id))
        except Cancelled:
            self._events.put(OpCancelled(task.task_id))
        except Exception as exc:
            if retries_left > 0:
                delay = 2 ** attempt  # 1s, 2s, 4s …
                threading.Timer(
                    delay,
                    self._pool.submit,
                    [self._run, task, retries_left - 1, attempt + 1],
                ).start()
                _retry_scheduled = True
            else:
                self._events.put(OpError(task.task_id, exc))
                with self._lock:
                    self._failed[task.task_id] = task
        finally:
            if not _retry_scheduled:
                with self._lock:
                    self._tasks.pop(task.task_id, None)
