"""Integration tests for fuzzy quick filter in DirSortFilterProxy."""
from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _items():
    return [
        FileItem(name="..", path=Path("/parent"), is_dir=True, size=0, modified=0.0),
        FileItem(name="hotel.txt", path=Path("/hotel.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="readme.md", path=Path("/readme.md"), is_dir=False, size=10, modified=0.0),
        FileItem(name="hotdog", path=Path("/hotdog"), is_dir=True, size=0, modified=0.0),
    ]


def _proxy(items):
    m = DirectoryModel()
    p = DirSortFilterProxy()
    p.setSourceModel(m)
    m.set_items(items)
    return p


def _visible(proxy):
    return [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]


def test_fuzzy_filter_shows_subsequence_match(qtbot):
    p = _proxy(_items())
    p.set_filter("htl")
    visible = _visible(p)
    assert "hotel.txt" in visible
    assert "readme.md" not in visible


def test_dotdot_always_visible(qtbot):
    p = _proxy(_items())
    p.set_filter("zzz")
    assert ".." in _visible(p)


def test_dirs_shown_in_fuzzy_mode(qtbot):
    p = _proxy(_items())
    p.set_filter("hotd")
    visible = _visible(p)
    assert "hotdog" in visible
    assert "hotel.txt" not in visible


def test_empty_query_shows_all(qtbot):
    p = _proxy(_items())
    p.set_filter("")
    assert p.rowCount() == 4  # .., hotel.txt, readme.md, hotdog


def test_case_insensitive(qtbot):
    p = _proxy(_items())
    p.set_filter("HTL")
    assert "hotel.txt" in _visible(p)
