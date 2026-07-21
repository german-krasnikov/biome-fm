"""Tests for SyncExecutor — covers copy and delete_orphan actions."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from biome_fm.presenters.sync_executor import SyncExecutor
from biome_fm.presenters.sync_presenter import SyncOp


class FakeVFS:
    def __init__(self) -> None:
        self.copied: list[tuple[Path, Path]] = []
        self.deleted: list[Path] = []

    def copy(self, src: Path, dst: Path) -> None:
        self.copied.append((src, dst))

    def delete(self, path: Path) -> None:
        self.deleted.append(path)


def make_executor(vfs: FakeVFS, progress=None) -> SyncExecutor:
    return SyncExecutor(vfs, threading.Event(), progress)


def test_copy_op_executed() -> None:
    vfs = FakeVFS()
    op = SyncOp(action="copy", src=Path("a.txt"), dst=Path("b/a.txt"), size=0)
    done = make_executor(vfs).execute([op])
    assert vfs.copied == [(Path("a.txt"), Path("b/a.txt"))]
    assert done == 1


def test_delete_orphan_actually_deletes() -> None:
    """RED: delete_orphan must call vfs.delete(src), not silently skip."""
    vfs = FakeVFS()
    # src=file to delete, dst=root dir (as built by sync_presenter)
    op = SyncOp(action="delete_orphan", src=Path("orphan.txt"), dst=Path("right_root"), size=0)
    done = make_executor(vfs).execute([op])
    assert vfs.deleted == [Path("orphan.txt")]
    assert done == 1


def test_delete_orphan_reports_progress() -> None:
    calls: list[tuple[int, int, str]] = []
    vfs = FakeVFS()
    op = SyncOp(action="delete_orphan", src=Path("x.txt"), dst=Path("right_root"), size=0)
    make_executor(vfs, progress=lambda d, t, n: calls.append((d, t, n))).execute([op])
    assert calls == [(1, 1, "x.txt")]


def test_cancel_stops_before_delete() -> None:
    vfs = FakeVFS()
    cancel = threading.Event()
    cancel.set()
    op = SyncOp(action="delete_orphan", src=Path("z.txt"), dst=Path("right_root"), size=0)
    done = SyncExecutor(vfs, cancel).execute([op])
    assert vfs.deleted == []
    assert done == 0


def test_mixed_ops_done_count() -> None:
    vfs = FakeVFS()
    ops = [
        SyncOp(action="copy", src=Path("a.txt"), dst=Path("dst/a.txt"), size=0),
        SyncOp(action="delete_orphan", src=Path("b.txt"), dst=Path("right_root"), size=0),
    ]
    done = make_executor(vfs).execute(ops)
    assert done == 2
    assert len(vfs.copied) == 1
    assert len(vfs.deleted) == 1
