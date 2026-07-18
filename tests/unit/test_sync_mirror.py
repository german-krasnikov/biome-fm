"""Unit tests for sync mirror mode (delete orphans)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.presenters.sync_presenter import preview_sync

LEFT = Path("/left")
RIGHT = Path("/right")


def _fi(name: str, root: Path, size: int = 100) -> FileItem:
    return FileItem(name=name, path=root / name, size=size, modified=0.0, is_dir=False)


def _entry(name: str, status: CompareStatus, *, left_root=LEFT, right_root=RIGHT) -> CompareEntry:
    left = _fi(name, left_root) if status not in {CompareStatus.RIGHT_ONLY} else None
    right = _fi(name, right_root) if status not in {CompareStatus.LEFT_ONLY} else None
    return CompareEntry(name=name, status=status, left=left, right=right)


# RED tests — all must fail before implementation


def test_orphan_deleted():
    """RIGHT_ONLY file with mirror=True/left_to_right → delete_orphan op."""
    entries = [_entry("orphan.txt", CompareStatus.RIGHT_ONLY)]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, mirror=True)
    assert len(ops) == 1
    assert ops[0].action == "delete_orphan"
    assert ops[0].src == RIGHT / "orphan.txt"
    assert ops[0].dst == RIGHT


def test_no_orphan_without_mirror():
    """RIGHT_ONLY with mirror=False → no ops (default behaviour preserved)."""
    entries = [_entry("orphan.txt", CompareStatus.RIGHT_ONLY)]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, mirror=False)
    assert ops == []


def test_mirror_preserves_copies():
    """mirror=True still emits copy ops for LEFT_ONLY and NEWER_LEFT."""
    entries = [
        _entry("new.txt", CompareStatus.LEFT_ONLY),
        _entry("updated.txt", CompareStatus.NEWER_LEFT),
    ]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, mirror=True)
    actions = [op.action for op in ops]
    assert actions.count("copy_left_to_right") == 2


def test_mirror_rtl_deletes_left_only():
    """RIGHT_TO_LEFT mirror: LEFT_ONLY entries → delete_orphan on left."""
    entries = [_entry("orphan.txt", CompareStatus.LEFT_ONLY)]
    ops = preview_sync(entries, "right_to_left", LEFT, RIGHT, mirror=True)
    assert len(ops) == 1
    assert ops[0].action == "delete_orphan"
    assert ops[0].src == LEFT / "orphan.txt"
    assert ops[0].dst == LEFT


def test_mirror_with_exclude_skips_excluded_orphans():
    """Excluded patterns still suppress delete_orphan ops."""
    entries = [
        _entry("skip.log", CompareStatus.RIGHT_ONLY),
        _entry("keep.txt", CompareStatus.RIGHT_ONLY),
    ]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, exclude=["*.log"], mirror=True)
    assert len(ops) == 1
    assert ops[0].src.name == "keep.txt"
