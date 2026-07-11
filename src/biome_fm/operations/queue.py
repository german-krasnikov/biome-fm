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
from biome_fm.operations.task import OpDone, OpError, OpEvent, OpStarted, OpTask

_id_gen = itertools.count(1)


class OpQueue:
    def __init__(self, max_workers: int = 2) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._events: queue.SimpleQueue[OpEvent] = queue.SimpleQueue()
        self._tasks: dict[int, OpTask] = {}
        self._lock = threading.Lock()

    def submit(self, cmd: Command) -> OpTask:
        task = OpTask(task_id=next(_id_gen), cmd=cmd)
        with self._lock:
            self._tasks[task.task_id] = task
        self._pool.submit(self._run, task)
        return task

    def cancel(self, task_id: int) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
        if task:
            task.cancel.set()

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

    def _run(self, task: OpTask) -> None:
        if task.cancel.is_set():
            return
        self._events.put(OpStarted(task.task_id))
        try:
            task.cmd.execute()
            self._events.put(OpDone(task.task_id))
        except Exception as exc:
            self._events.put(OpError(task.task_id, exc))
        finally:
            with self._lock:
                self._tasks.pop(task.task_id, None)
