"""Unit tests for sync exclude-pattern filtering (F026)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.presenters.sync_presenter import preview_sync

LEFT = Path("/left")
RIGHT = Path("/right")


def _fi(name: str) -> FileItem:
    return FileItem(name=name, path=LEFT / name, is_dir=False, size=100, modified=1.0)


def _entry(name: str, status: CompareStatus = CompareStatus.LEFT_ONLY) -> CompareEntry:
    return CompareEntry(name=name, status=status, left=_fi(name))


def test_no_excludes_includes_all():
    entries = [_entry("a.txt"), _entry("b.log")]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT)
    assert len(ops) == 2


def test_excluded_pattern_skipped():
    entries = [_entry("a.txt"), _entry("b.log")]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, exclude=["*.log"])
    names = [op.src.name for op in ops]
    assert "b.log" not in names
    assert "a.txt" in names


def test_multiple_excludes_all_applied():
    entries = [_entry("a.txt"), _entry("b.log"), _entry("node_modules")]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, exclude=["*.log", "node_modules"])
    names = [op.src.name for op in ops]
    assert "b.log" not in names
    assert "node_modules" not in names
    assert "a.txt" in names


def test_exclude_directory_by_name():
    entries = [_entry("src"), _entry("node_modules"), _entry("dist")]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, exclude=["node_modules"])
    names = [op.src.name for op in ops]
    assert "node_modules" not in names
    assert "src" in names
    assert "dist" in names


def test_exclude_with_wildcard():
    entries = [_entry("main.py"), _entry("main.pyc"), _entry("cache.pyc")]
    ops = preview_sync(entries, "left_to_right", LEFT, RIGHT, exclude=["*.pyc"])
    names = [op.src.name for op in ops]
    assert "main.pyc" not in names
    assert "cache.pyc" not in names
    assert "main.py" in names
