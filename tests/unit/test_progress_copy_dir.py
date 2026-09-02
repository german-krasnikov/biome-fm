"""#53 — Dir Copy Progress Fix: _copy_dir replaces shutil.copytree with progress."""
import os
import threading
import time

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.models.conflict_resolver import ConflictAction
from biome_fm.models.vfs import LocalVFS
from biome_fm.operations.task import Cancelled


def test_dir_progress_reported(tmp_path):
    src = tmp_path / "srcdir"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello")
    dst = tmp_path / "dst"
    dst.mkdir()

    reports = []
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: reports.append(a))
    cmd.execute()

    assert (dst / "srcdir" / "a.txt").read_bytes() == b"hello"
    assert len(reports) > 0


def test_nested_dirs(tmp_path):
    src = tmp_path / "root"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "b.txt").write_bytes(b"world")
    dst = tmp_path / "dst"
    dst.mkdir()

    reports = []
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst, None, cancel, lambda *a: reports.append(a))
    cmd.execute()

    assert (dst / "root" / "sub" / "b.txt").read_bytes() == b"world"
    assert len(reports) > 0


def test_overwrite_dir_replaces_smaller_newer_child(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_parent = tmp_path / "dst_parent"
    dst_parent.mkdir()
    dst = dst_parent / "src"
    dst.mkdir()
    # child in src (1200 B)
    (src / "f.txt").write_bytes(b"X" * 1200)
    # child in dst (900 B, newer mtime — triggers resume heuristic)
    dst_child = dst / "f.txt"
    dst_child.write_bytes(b"O" * 900)
    os.utime(dst_child, (time.time() + 100,) * 2)

    ProgressCopyCmd(
        [src], dst_parent, LocalVFS(), threading.Event(),
        lambda *a: None, strategy=ConflictAction.OVERWRITE_ALL,
    ).execute()

    assert (dst / "f.txt").read_bytes() == b"X" * 1200


def test_merge_copy_cancel_keeps_preexisting(tmp_path):
    src = tmp_path / "proj"
    src.mkdir()
    (src / "new.txt").write_bytes(b"new")
    dest_parent = tmp_path / "dest_parent"
    dest_parent.mkdir()
    dst = dest_parent / "proj"
    dst.mkdir()  # pre-existing dir distinct from src
    keep = dst / "keep.txt"
    keep.write_bytes(b"precious")
    calls = []

    def report(*a):
        calls.append(a)
        if len(calls) > 1:
            raise Cancelled()

    cmd = ProgressCopyCmd([src], dest_parent, LocalVFS(), threading.Event(), report)
    with pytest.raises(Cancelled):
        cmd.execute()
    assert keep.exists() and keep.read_bytes() == b"precious"


