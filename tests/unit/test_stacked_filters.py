"""Unit tests for F291 — Incremental Narrowing (Stacked Filters)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _items():
    return [
        FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0),
        FileItem(name="foobar.py", path=Path("/foobar.py"), is_dir=False, size=0, modified=0.0),
        FileItem(name="foo.txt", path=Path("/foo.txt"), is_dir=False, size=0, modified=0.0),
        FileItem(name="bar.py", path=Path("/bar.py"), is_dir=False, size=0, modified=0.0),
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


def test_push_filter_narrows(proxy):
    proxy.set_filter("foo")      # matches foobar.py + foo.txt
    before = proxy.rowCount()
    proxy.push_filter("py")      # now requires both "foo" AND "py" → only foobar.py
    assert proxy.rowCount() < before
    assert "foobar.py" in _names(proxy)
    assert "foo.txt" not in _names(proxy)


def test_pop_filter_widens(proxy):
    proxy.set_filter("foo")
    proxy.push_filter("py")      # narrow: only foobar.py
    narrow = proxy.rowCount()
    proxy.pop_filter()           # widen: back to foo-only
    assert proxy.rowCount() > narrow


def test_set_filter_replaces_stack(proxy):
    proxy.push_filter("foo")
    proxy.push_filter("bar")     # stack=["foo","bar"] → only foobar.py matches
    stacked = proxy.rowCount()
    proxy.set_filter("bar")      # replaces stack → foobar.py + bar.py
    assert proxy.rowCount() > stacked
    assert "bar.py" in _names(proxy)
