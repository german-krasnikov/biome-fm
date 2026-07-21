"""Tests for SyncExecutor — RED phase."""
from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from biome_fm.presenters.sync_executor import SyncExecutor
from biome_fm.presenters.sync_presenter import SyncOp

_A = Path("/src/a.txt")
_B = Path("/src/b.txt")
_DST = Path("/dst")


def _op(action: str, src: Path = _A, dst: Path = _DST) -> SyncOp:
    return SyncOp(action=action, src=src, dst=dst)


def test_execute_sync_copies_files():
    vfs = MagicMock()
    cancel = threading.Event()
    ops = [_op("copy_left_to_right", _A), _op("copy_left_to_right", _B)]
    count = SyncExecutor(vfs, cancel).execute(ops)
    assert count == 2
    assert vfs.copy.call_args_list == [call(_A, _DST), call(_B, _DST)]


def test_execute_sync_deletes_orphan():
    vfs = MagicMock()
    cancel = threading.Event()
    ops = [_op("delete_orphan"), _op("copy_left_to_right", _B)]
    count = SyncExecutor(vfs, cancel).execute(ops)
    assert count == 2
    vfs.delete.assert_called_once_with(_A)
    vfs.copy.assert_called_once_with(_B, _DST)


def test_execute_sync_with_cancel():
    vfs = MagicMock()
    cancel = threading.Event()
    ops = [_op("copy_left_to_right", _A), _op("copy_left_to_right", _B)]
    # Set cancel after first call via side_effect
    def _copy_and_cancel(src, dst):
        cancel.set()
    vfs.copy.side_effect = _copy_and_cancel
    count = SyncExecutor(vfs, cancel).execute(ops)
    assert count == 1
    vfs.copy.assert_called_once_with(_A, _DST)


def test_execute_sync_reports_progress():
    vfs = MagicMock()
    cancel = threading.Event()
    ops = [_op("copy_left_to_right", _A), _op("copy_right_to_left", _B)]
    calls: list[tuple] = []
    SyncExecutor(vfs, cancel, progress=lambda *a: calls.append(a)).execute(ops)
    assert calls == [(1, 2, _A.name), (2, 2, _B.name)]


def test_execute_sync_empty_ops():
    vfs = MagicMock()
    cancel = threading.Event()
    count = SyncExecutor(vfs, cancel).execute([])
    assert count == 0
    vfs.copy.assert_not_called()
