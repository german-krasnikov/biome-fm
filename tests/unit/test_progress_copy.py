"""Tests for ProgressCopyCmd — chunk copy with progress + cancel."""
import threading

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.operations.task import Cancelled


def test_progress_copy_creates_file(tmp_path):
    src = tmp_path / "a.txt"
    src.write_bytes(b"hello world")
    dst = tmp_path / "dst"
    dst.mkdir()
    cancel = threading.Event()
    events = []
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: events.append(a))
    cmd.execute()
    assert (dst / "a.txt").read_bytes() == b"hello world"
    assert len(events) > 0


def test_progress_copy_reports_progress(tmp_path):
    src = tmp_path / "big.bin"
    src.write_bytes(b"x" * 100_000)
    dst = tmp_path / "dst"
    dst.mkdir()
    cancel = threading.Event()
    events = []
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: events.append(a), chunk=10_000)
    cmd.execute()
    assert len(events) >= 10


def test_progress_copy_cancel_cleans_up(tmp_path):
    src = tmp_path / "big.bin"
    src.write_bytes(b"x" * 1_000_000)
    dst = tmp_path / "dst"
    dst.mkdir()
    cancel = threading.Event()
    count = [0]

    def report(*a):
        count[0] += 1
        if count[0] == 2:
            cancel.set()

    with pytest.raises(Cancelled):
        ProgressCopyCmd([src], dst, None, cancel, report, chunk=10_000).execute()
    assert not (dst / "big.bin").exists()


def test_progress_copy_undo(tmp_path):
    src = tmp_path / "f.txt"
    src.write_text("data")
    dst = tmp_path / "dst"
    dst.mkdir()
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *_: None)
    cmd.execute()
    assert (dst / "f.txt").exists()
    cmd.undo()
    assert not (dst / "f.txt").exists()


def test_progress_copy_dir(tmp_path):
    src = tmp_path / "mydir"
    src.mkdir()
    (src / "child.txt").write_text("hi")
    dst = tmp_path / "dst"
    dst.mkdir()
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *_: None)
    cmd.execute()
    assert (dst / "mydir" / "child.txt").read_text() == "hi"
