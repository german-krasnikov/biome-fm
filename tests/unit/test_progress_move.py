"""Tests for ProgressMoveCmd."""
import threading
from unittest.mock import MagicMock

import pytest

from biome_fm.commands.move_cmd import ProgressMoveCmd
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
