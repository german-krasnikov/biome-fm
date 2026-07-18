"""Unit tests for F284 — Sticky Selection Filter (Show Only Marked)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _items():
    return [
        FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0),
        FileItem(name="file1.txt", path=Path("/file1.txt"), is_dir=False, size=0, modified=0.0),
        FileItem(name="file2.txt", path=Path("/file2.txt"), is_dir=False, size=0, modified=0.0),
    ]


@pytest.fixture
def proxy(qtbot):
    m = DirectoryModel()
    p = DirSortFilterProxy()
    p.setSourceModel(m)
    m.set_items(_items())
    return p


def _names(proxy):
    return [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]


def test_show_only_marked_filters(proxy):
    proxy.set_marked_paths({Path("/file1.txt")})
    proxy.set_show_only_marked(True)
    names = _names(proxy)
    assert "file1.txt" in names
    assert "file2.txt" not in names
    assert ".." in names  # always shown


def test_toggle_off_shows_all(proxy):
    proxy.set_marked_paths({Path("/file1.txt")})
    proxy.set_show_only_marked(True)
    proxy.set_show_only_marked(False)
    names = _names(proxy)
    assert "file1.txt" in names
    assert "file2.txt" in names
