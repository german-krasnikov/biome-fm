"""Unit tests for content_diff in ComparePresenter."""
from __future__ import annotations

from pathlib import Path

import pytest


def _make_item(path: Path, size: int = 0, modified: float = 0.0):
    from biome_fm.models.file_item import FileItem
    return FileItem(name=path.name, path=path, is_dir=False, size=size, modified=modified)


def test_equal_files_empty(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("same\ncontent\n")
    b.write_text("same\ncontent\n")
    from biome_fm.presenters.compare_presenter import ComparePresenter, CompareEntry, CompareStatus
    entry = CompareEntry(name="a.txt", status=CompareStatus.EQUAL,
                         left=_make_item(a), right=_make_item(b))
    diff = ComparePresenter.content_diff(entry)
    assert diff == ""


def test_modified_shows_diff(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("line1\nline2\n")
    b.write_text("line1\nchanged\n")
    from biome_fm.presenters.compare_presenter import ComparePresenter, CompareEntry, CompareStatus
    entry = CompareEntry(name="a.txt", status=CompareStatus.DIFF_SIZE,
                         left=_make_item(a), right=_make_item(b))
    diff = ComparePresenter.content_diff(entry)
    assert "-line2" in diff
    assert "+changed" in diff


def test_binary_skipped(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(bytes(range(256)))
    b.write_bytes(bytes(range(1, 256)) + b"\x00")
    from biome_fm.presenters.compare_presenter import ComparePresenter, CompareEntry, CompareStatus
    entry = CompareEntry(name="a.bin", status=CompareStatus.DIFF_SIZE,
                         left=_make_item(a), right=_make_item(b))
    diff = ComparePresenter.content_diff(entry)
    assert "binary" in diff.lower() or diff == ""


def test_missing_side_graceful(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("only left\n")
    from biome_fm.presenters.compare_presenter import ComparePresenter, CompareEntry, CompareStatus
    entry = CompareEntry(name="a.txt", status=CompareStatus.LEFT_ONLY,
                         left=_make_item(a), right=None)
    diff = ComparePresenter.content_diff(entry)
    assert diff == ""
