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


# --- undo() backup/restore tests ---

def test_overwrite_undo_restores_original(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new content")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("original content")
    cancel = threading.Event()
    cmd = ProgressCopyCmd(
        [src], dst_dir, None, cancel, lambda *_: None,
        conflict_resolver=_resolver(ConflictAction.OVERWRITE),
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "new content"
    cmd.undo()
    assert (dst_dir / "a.txt").read_text() == "original content"


def test_overwrite_all_undo_restores_all(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    names = ["a.txt", "b.txt", "c.txt"]
    for n in names:
        (src_dir / n).write_text(f"new_{n}")
        (dst_dir / n).write_text(f"orig_{n}")
    cancel = threading.Event()
    cmd = ProgressCopyCmd(
        [src_dir / n for n in names], dst_dir, None, cancel, lambda *_: None,
        conflict_resolver=_resolver(ConflictAction.OVERWRITE_ALL),
    )
    cmd.execute()
    cmd.undo()
    for n in names:
        assert (dst_dir / n).read_text() == f"orig_{n}"


def test_overwrite_cancel_mid_copy_restores_original(tmp_path):
    src = tmp_path / "big.bin"
    src.write_bytes(b"X" * 1_000_000)
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    original = b"original data"
    (dst_dir / "big.bin").write_bytes(original)
    cancel = threading.Event()
    call_count = [0]

    def report(*a):
        call_count[0] += 1
        if call_count[0] == 2:
            cancel.set()

    cmd = ProgressCopyCmd(
        [src], dst_dir, None, cancel, report, chunk=10_000,
        conflict_resolver=_resolver(ConflictAction.OVERWRITE),
    )
    with pytest.raises(Cancelled):
        cmd.execute()
    assert (dst_dir / "big.bin").read_bytes() == original


def test_no_backup_when_dst_is_new(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("data")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    cancel = threading.Event()
    cmd = ProgressCopyCmd([src], dst_dir, None, cancel, lambda *_: None)
    cmd.execute()
    assert cmd._backups == {}
    cmd.undo()
    assert not (dst_dir / "a.txt").exists()


def test_skip_action_leaves_original_and_no_backup(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("orig")
    cancel = threading.Event()
    cmd = ProgressCopyCmd(
        [src], dst_dir, None, cancel, lambda *_: None,
        conflict_resolver=_resolver(ConflictAction.SKIP),
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "orig"
    assert cmd._backups == {}


def test_no_temp_files_leak_after_undo(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("new")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("orig")
    cancel = threading.Event()
    cmd = ProgressCopyCmd(
        [src], dst_dir, None, cancel, lambda *_: None,
        conflict_resolver=_resolver(ConflictAction.OVERWRITE),
    )
    cmd.execute()
    cmd.undo()
    bak_files = [p for p in dst_dir.iterdir() if ".biome_bak_" in p.name]
    assert bak_files == []
    assert cmd._backups == {}
