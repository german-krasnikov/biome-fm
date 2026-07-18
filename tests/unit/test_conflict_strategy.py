"""Tests for pre-copy conflict strategy resolver (F066)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.conflict_resolver import ConflictAction, ConflictResolver, PreCopyConflictResolver

_SRC = Path("/src/a.txt")
_DST = Path("/dst/a.txt")


def test_skip_all_strategy_skips_all_conflicts():
    r = PreCopyConflictResolver(ConflictAction.SKIP_ALL)
    assert r.ask(_SRC, _DST) == ConflictAction.SKIP_ALL
    assert r.ask(_SRC, _DST) == ConflictAction.SKIP_ALL  # idempotent


def test_overwrite_all_strategy_overwrites_all():
    r = PreCopyConflictResolver(ConflictAction.OVERWRITE_ALL)
    assert r.ask(_SRC, _DST) == ConflictAction.OVERWRITE_ALL
    assert r.ask(Path("/src/b.txt"), Path("/dst/b.txt")) == ConflictAction.OVERWRITE_ALL


def test_rename_all_strategy_renames_all():
    r = PreCopyConflictResolver(ConflictAction.RENAME)
    assert r.ask(_SRC, _DST) == ConflictAction.RENAME
    assert r.ask(Path("/src/b.txt"), Path("/dst/b.txt")) == ConflictAction.RENAME


def test_ask_each_falls_through_to_resolver():
    fallback = MagicMock(spec=ConflictResolver)
    fallback.ask.return_value = ConflictAction.OVERWRITE
    r = PreCopyConflictResolver(ConflictAction.ASK_EACH, fallback=fallback)
    result = r.ask(_SRC, _DST)
    fallback.ask.assert_called_once_with(_SRC, _DST)
    assert result == ConflictAction.OVERWRITE


def test_ask_each_without_fallback_cancels():
    r = PreCopyConflictResolver(ConflictAction.ASK_EACH)
    assert r.ask(_SRC, _DST) == ConflictAction.CANCEL


def test_progress_copy_skip_all_skips_conflicts(tmp_path):
    """strategy=SKIP_ALL skips conflicting files during actual copy."""
    import threading
    from biome_fm.commands.copy_cmd import ProgressCopyCmd
    from biome_fm.models.vfs import LocalVFS

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("new-a")
    (src_dir / "b.txt").write_text("new-b")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old-a")  # conflict

    cmd = ProgressCopyCmd(
        sources=[src_dir / "a.txt", src_dir / "b.txt"],
        dest_dir=dst_dir,
        vfs=LocalVFS(),
        cancel=threading.Event(),
        report=lambda *_: None,
        strategy=ConflictAction.SKIP_ALL,
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "old-a"  # skipped, not overwritten
    assert (dst_dir / "b.txt").read_text() == "new-b"  # no conflict, copied


def test_progress_copy_overwrite_all_overwrites(tmp_path):
    """strategy=OVERWRITE_ALL overwrites conflicting files."""
    import threading
    from biome_fm.commands.copy_cmd import ProgressCopyCmd
    from biome_fm.models.vfs import LocalVFS

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("new-a")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    (dst_dir / "a.txt").write_text("old-a")

    cmd = ProgressCopyCmd(
        sources=[src_dir / "a.txt"],
        dest_dir=dst_dir,
        vfs=LocalVFS(),
        cancel=threading.Event(),
        report=lambda *_: None,
        strategy=ConflictAction.OVERWRITE_ALL,
    )
    cmd.execute()
    assert (dst_dir / "a.txt").read_text() == "new-a"
