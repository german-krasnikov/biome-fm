"""Unit tests for pause/resume/retry/skip in OpQueue + ProgressCopyCmd."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from biome_fm.commands.base import Command
from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.operations.queue import OpQueue
from biome_fm.operations.task import OpError


class _FailCmd(Command):
    def execute(self) -> None:
        raise RuntimeError("boom")

    def undo(self) -> None: ...


class _OkCmd(Command):
    executed = False

    def execute(self) -> None:
        self.executed = True

    def undo(self) -> None: ...


def _noop(*_: object) -> None: ...


def test_pause_blocks_chunk_iteration(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_bytes(b"x" * 10)
    dst = tmp_path / "dst.txt"
    pause = threading.Event()  # not set = paused
    cancel = threading.Event()
    done_evt = threading.Event()

    cmd = ProgressCopyCmd([src], tmp_path, None, cancel, _noop, pause=pause)

    def _run() -> None:
        cmd._copy_file(src, dst)
        done_evt.set()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.05)
    assert not done_evt.is_set(), "copy should be blocked while paused"
    pause.set()
    assert done_evt.wait(timeout=2), "copy should complete after resume"


def test_resume_after_pause_continues(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    data = b"hello world"
    src.write_bytes(data)
    dst = tmp_path / "out.txt"
    pause = threading.Event()  # starts paused
    cancel = threading.Event()

    cmd = ProgressCopyCmd([src], tmp_path, None, cancel, _noop, pause=pause)
    t = threading.Thread(target=lambda: cmd._copy_file(src, dst), daemon=True)
    t.start()
    time.sleep(0.02)
    pause.set()
    t.join(timeout=2)
    assert dst.read_bytes() == data


def test_retry_resubmits_after_error() -> None:
    q = OpQueue(max_workers=1)
    cmd = _FailCmd()
    task = q.submit(cmd)
    time.sleep(0.15)
    events = q.drain()
    assert any(isinstance(e, OpError) and e.task_id == task.task_id for e in events)
    assert task.task_id in q._failed

    q.retry(task.task_id)
    time.sleep(0.15)
    events2 = q.drain()
    assert any(isinstance(e, OpError) and e.task_id == task.task_id for e in events2)
    q.shutdown(wait=False)


def test_cancel_while_paused_unblocks_and_cancels(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_bytes(b"x" * 100)
    dst = tmp_path / "dst.txt"
    pause = threading.Event()  # not set = paused
    cancel = threading.Event()
    from biome_fm.operations.task import Cancelled

    cmd = ProgressCopyCmd([src], tmp_path, None, cancel, _noop, pause=pause)
    exc_holder: list[Exception] = []

    def _run() -> None:
        try:
            cmd._copy_file(src, dst)
        except Cancelled:
            exc_holder.append(Cancelled())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    time.sleep(0.05)
    # Task is paused. Cancel should unblock it.
    pause.set()
    cancel.set()
    t.join(timeout=2)
    assert len(exc_holder) == 1, "cancel while paused should raise Cancelled"


def test_skip_on_error_removes_from_failed() -> None:
    q = OpQueue(max_workers=1)
    task = q.submit(_FailCmd())
    time.sleep(0.15)
    q.drain()
    assert task.task_id in q._failed
    q.skip(task.task_id)
    assert task.task_id not in q._failed
    q.shutdown(wait=False)
