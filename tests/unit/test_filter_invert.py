"""Unit tests for DirSortFilterProxy inversion (F228)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem


def _items():
    return [
        FileItem(name="..", path=Path("/parent"), is_dir=True, size=0, modified=0.0),
        FileItem(name="test_a.txt", path=Path("/test_a.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="test_b.txt", path=Path("/test_b.txt"), is_dir=False, size=10, modified=0.0),
        FileItem(name="other.txt", path=Path("/other.txt"), is_dir=False, size=10, modified=0.0),
    ]


def _make_proxy():
    model = DirectoryModel()
    proxy = DirSortFilterProxy()
    proxy.setSourceModel(model)
    model.set_items(_items())
    return proxy


def test_invert_hides_matching(qtbot):
    proxy = _make_proxy()
    proxy.set_filter("test")
    proxy.set_invert(True)
    names = [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]
    assert "test_a.txt" not in names
    assert "test_b.txt" not in names
    assert "other.txt" in names
    assert ".." in names  # dotdot always shown


def test_invert_no_filter_shows_all(qtbot):
    proxy = _make_proxy()
    proxy.set_invert(True)
    # no filter → show all regardless of invert
    assert proxy.rowCount() == 4


def test_invert_toggle_off(qtbot):
    proxy = _make_proxy()
    proxy.set_filter("test")
    proxy.set_invert(True)
    proxy.set_invert(False)
    names = [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]
    assert "test_a.txt" in names
    assert "test_b.txt" in names
    assert "other.txt" not in names
