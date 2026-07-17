"""Tests for ProgressCopyCmd conflict resolution."""
import threading

import pytest

from biome_fm.commands.copy_cmd import ProgressCopyCmd
from biome_fm.models.conflict_resolver import ConflictAction, ConflictResolver
from biome_fm.operations.task import Cancelled


def _resolver(action: ConflictAction) -> ConflictResolver:
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(action)
    return r


def test_dst_exists_overwrite(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old")
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None,
                          conflict_resolver=_resolver(ConflictAction.OVERWRITE))
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "new"


def test_dst_exists_skip(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old")
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None,
                          conflict_resolver=_resolver(ConflictAction.SKIP))
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "old"


def test_dst_exists_rename(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old")
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None,
                          conflict_resolver=_resolver(ConflictAction.RENAME))
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "old"    # original unchanged
    assert (dst_dir / "a_1.txt").read_text() == "new"  # written to renamed path


def test_dst_exists_cancel(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old")
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None,
                          conflict_resolver=_resolver(ConflictAction.CANCEL))
    with pytest.raises(Cancelled):
        cmd.execute()


def test_no_conflict_resolver_not_called(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    cancel = threading.Event()
    called = []
    r = ConflictResolver()
    r.on_conflict = lambda *_: called.append(1)
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None,
                          conflict_resolver=r)
    cmd.execute()
    assert not called  # dst didn't exist → resolver never asked
