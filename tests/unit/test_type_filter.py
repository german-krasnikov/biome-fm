"""Unit tests for F217 — Quick Filter Type Toggle (Files/Dirs/All)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _items():
    return [
        FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0),
        FileItem(name="folder", path=Path("/folder"), is_dir=True, size=0, modified=0.0),
        FileItem(name="file.txt", path=Path("/file.txt"), is_dir=False, size=10, modified=0.0),
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


def test_filter_files_only(proxy):
    proxy.set_type_filter("files")
    names = _names(proxy)
    assert "folder" not in names
    assert "file.txt" in names


def test_filter_dirs_only(proxy):
    proxy.set_type_filter("dirs")
    names = _names(proxy)
    assert "folder" in names
    assert "file.txt" not in names


def test_filter_all(proxy):
    proxy.set_type_filter("all")
    names = _names(proxy)
    assert "folder" in names
    assert "file.txt" in names


def test_dotdot_always_shown(proxy):
    proxy.set_type_filter("files")
    assert ".." in _names(proxy)
