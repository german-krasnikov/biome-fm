"""TDD: build_sync_commands pure-Python sync logic."""
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.presenters.sync_presenter import build_sync_commands

LEFT_ROOT = Path("/left")
RIGHT_ROOT = Path("/right")


def _item(name: str, root: Path, *, size: int = 100, mtime: float = 1.0) -> FileItem:
    return FileItem(name=name, path=root / name, is_dir=False, size=size, modified=mtime)


def _entry(name: str, status: CompareStatus, left=None, right=None) -> CompareEntry:
    return CompareEntry(name=name, status=status, left=left, right=right)


def test_empty_entries():
    assert build_sync_commands([], "left_to_right", LEFT_ROOT, RIGHT_ROOT) == []


def test_equal_skipped():
    lf = _item("a.txt", LEFT_ROOT)
    rf = _item("a.txt", RIGHT_ROOT)
    e = _entry("a.txt", CompareStatus.EQUAL, lf, rf)
    assert build_sync_commands([e], "left_to_right", LEFT_ROOT, RIGHT_ROOT) == []


def test_left_only_copies_to_right():
    lf = _item("a.txt", LEFT_ROOT)
    e = _entry("a.txt", CompareStatus.LEFT_ONLY, left=lf)
    cmds = build_sync_commands([e], "left_to_right", LEFT_ROOT, RIGHT_ROOT)
    assert cmds == [(lf.path, RIGHT_ROOT)]


def test_right_only_copies_to_left():
    rf = _item("b.txt", RIGHT_ROOT)
    e = _entry("b.txt", CompareStatus.RIGHT_ONLY, right=rf)
    cmds = build_sync_commands([e], "right_to_left", LEFT_ROOT, RIGHT_ROOT)
    assert cmds == [(rf.path, LEFT_ROOT)]


def test_newer_wins_both_directions():
    lf = _item("c.txt", LEFT_ROOT)
    rf = _item("d.txt", RIGHT_ROOT)
    entries = [
        _entry("c.txt", CompareStatus.NEWER_LEFT, left=lf, right=_item("c.txt", RIGHT_ROOT)),
        _entry("d.txt", CompareStatus.NEWER_RIGHT, left=_item("d.txt", LEFT_ROOT), right=rf),
    ]
    cmds = build_sync_commands(entries, "newer_wins", LEFT_ROOT, RIGHT_ROOT)
    assert (lf.path, RIGHT_ROOT) in cmds
    assert (rf.path, LEFT_ROOT) in cmds
