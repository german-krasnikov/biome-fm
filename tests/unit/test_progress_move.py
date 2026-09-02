"""Tests for ProgressMoveCmd."""
import threading
from unittest.mock import MagicMock

import pytest

from biome_fm.commands.move_cmd import ProgressMoveCmd
from biome_fm.models.conflict_resolver import ConflictAction, PreCopyConflictResolver
from biome_fm.models.vfs import LocalVFS
from biome_fm.operations.task import Cancelled


def test_progress_move(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("data")
    dst = tmp_path / "dst"
    dst.mkdir()
    vfs = MagicMock()
    vfs.move.side_effect = lambda s, d: s.rename(d)
    cancel = threading.Event()
    events = []
    cmd = ProgressMoveCmd([src], dst, vfs, cancel, lambda *a: events.append(a))
    cmd.execute()
    assert len(events) == 1


def test_progress_move_cancel(tmp_path):
    src1 = tmp_path / "a.txt"
    src1.write_text("a")
    src2 = tmp_path / "b.txt"
    src2.write_text("b")
    dst = tmp_path / "dst"
    dst.mkdir()
    vfs = MagicMock()
    cancel = threading.Event()
    cancel.set()  # pre-cancelled
    with pytest.raises(Cancelled):
        ProgressMoveCmd([src1, src2], dst, vfs, cancel, lambda *_: None).execute()


def test_progress_move_undo(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("data")
    dst = tmp_path / "dst"
    dst.mkdir()
    vfs = MagicMock()
    vfs.move.side_effect = lambda s, d: s.rename(d)
    cancel = threading.Event()
    cmd = ProgressMoveCmd([src], dst, vfs, cancel, lambda *_: None)
    cmd.execute()
    assert not src.exists()
    vfs.move.side_effect = lambda s, d: s.rename(d)
    cmd.undo()


def test_overwrite_move_replaces_dst(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    existing = dst_dir / "a.txt"
    existing.write_text("old")
    cmd = ProgressMoveCmd(
        [src], dst_dir, LocalVFS(), threading.Event(), lambda *a: None,
        conflict_resolver=PreCopyConflictResolver(ConflictAction.OVERWRITE),
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "new"
    assert not src.exists()
