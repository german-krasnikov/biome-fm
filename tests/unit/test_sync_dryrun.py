"""Unit tests for sync dry-run / preview_sync — no Qt, no filesystem writes."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.presenters.sync_presenter import SyncOp, build_sync_commands, preview_sync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fi(name: str, root: Path, size: int = 100) -> FileItem:
    return FileItem(name=name, path=root / name, is_dir=False, size=size, modified=0.0)


def _entry(
    name: str,
    status: CompareStatus,
    left: FileItem | None = None,
    right: FileItem | None = None,
) -> CompareEntry:
    return CompareEntry(name=name, status=status, left=left, right=right)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_dry_run_no_side_effects(tmp_path: Path) -> None:
    """preview_sync must not create, delete, or modify any files."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()

    entries = [
        _entry("a.txt", CompareStatus.LEFT_ONLY, left=_fi("a.txt", left_root)),
        _entry("b.txt", CompareStatus.RIGHT_ONLY, right=_fi("b.txt", right_root)),
    ]

    before_left = set(left_root.iterdir())
    before_right = set(right_root.iterdir())

    preview_sync(entries, "left_to_right", left_root, right_root)

    assert set(left_root.iterdir()) == before_left
    assert set(right_root.iterdir()) == before_right


def test_dry_run_returns_correct_op_list(tmp_path: Path) -> None:
    """preview_sync returns SyncOp with correct action, src, dst for left_to_right."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"

    fi = _fi("a.txt", left_root, size=42)
    entries = [_entry("a.txt", CompareStatus.LEFT_ONLY, left=fi)]

    ops = preview_sync(entries, "left_to_right", left_root, right_root)

    assert len(ops) == 1
    op = ops[0]
    assert isinstance(op, SyncOp)
    assert op.action == "copy_left_to_right"
    assert op.src == fi.path
    assert op.dst == right_root
    assert op.size == 42


def test_dry_run_shows_copy_and_delete_ops(tmp_path: Path) -> None:
    """newer_wins with left-only and right-only files → ops for both directions."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"

    entries = [
        _entry("only_left.txt", CompareStatus.LEFT_ONLY, left=_fi("only_left.txt", left_root)),
        _entry("only_right.txt", CompareStatus.RIGHT_ONLY, right=_fi("only_right.txt", right_root)),
    ]

    ops = preview_sync(entries, "newer_wins", left_root, right_root)

    actions = {op.action for op in ops}
    assert "copy_left_to_right" in actions
    assert "copy_right_to_left" in actions


def test_dry_run_empty_dirs_no_ops(tmp_path: Path) -> None:
    """Two identical dirs (all EQUAL) → empty op list."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"

    entries = [
        _entry("same.txt", CompareStatus.EQUAL,
               left=_fi("same.txt", left_root),
               right=_fi("same.txt", right_root)),
    ]

    ops = preview_sync(entries, "left_to_right", left_root, right_root)
    assert ops == []


def test_newer_wins_diff_size_picks_newer_mtime(tmp_path: Path) -> None:
    """DIFF_SIZE entries use mtime to decide direction in newer_wins."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_fi = FileItem(name="f.txt", path=left_root / "f.txt", is_dir=False, size=200, modified=100.0)
    right_fi = FileItem(name="f.txt", path=right_root / "f.txt", is_dir=False, size=100, modified=50.0)
    entries = [_entry("f.txt", CompareStatus.DIFF_SIZE, left=left_fi, right=right_fi)]
    ops = preview_sync(entries, "newer_wins", left_root, right_root)
    assert len(ops) == 1
    assert ops[0].action == "copy_left_to_right"


def test_normal_run_still_executes(tmp_path: Path) -> None:
    """build_sync_commands still returns SyncPair list as before (backward compat)."""
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"

    fi = _fi("x.txt", left_root, size=10)
    entries = [_entry("x.txt", CompareStatus.LEFT_ONLY, left=fi)]

    pairs = build_sync_commands(entries, "left_to_right", left_root, right_root)

    assert len(pairs) == 1
    src, dst = pairs[0]
    assert src == fi.path
    assert dst == right_root
