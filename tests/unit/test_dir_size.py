"""Tests for dir_size utility — TDD red phase."""
from __future__ import annotations
import time
import threading
from pathlib import Path

import pytest


def test_single_file(tmp_path: Path) -> None:
    from biome_fm.utils.dir_size import calc_tree_size
    f = tmp_path / "a.txt"
    f.write_bytes(b"hello")
    assert calc_tree_size([f], [False]) == 5


def test_recursive_dir(tmp_path: Path) -> None:
    from biome_fm.utils.dir_size import calc_tree_size
    (tmp_path / "a.txt").write_bytes(b"ab")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_bytes(b"cde")
    assert calc_tree_size([tmp_path], [False]) == 5


def test_cancel_returns_minus_one(tmp_path: Path) -> None:
    from biome_fm.utils.dir_size import calc_tree_size
    (tmp_path / "x.txt").write_bytes(b"x" * 100)
    cancel = [True]
    assert calc_tree_size([tmp_path], cancel) == -1


def test_empty_dir(tmp_path: Path) -> None:
    from biome_fm.utils.dir_size import calc_tree_size
    assert calc_tree_size([tmp_path], [False]) == 0


def test_permission_error_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from biome_fm.utils import dir_size as ds
    f = tmp_path / "secret.txt"
    f.write_bytes(b"data")

    real_stat = ds.os.stat

    def bad_stat(path, **kw):  # type: ignore[no-untyped-def]
        raise OSError("Permission denied")

    monkeypatch.setattr(ds.os, "stat", bad_stat)
    result = ds.calc_tree_size([tmp_path], [False])
    assert result == 0  # skipped, no crash


def test_presenter_sets_dir_size_result(tmp_path: Path) -> None:
    """_start_dir_size_calc sets _dir_size_result after background thread completes."""
    from biome_fm.utils.dir_size import calc_tree_size  # noqa: F401
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.file_item import FileItem
    from biome_fm.models.vfs import LocalVFS

    # build a tiny dir with known content
    d = tmp_path / "mydir"
    d.mkdir()
    (d / "file.txt").write_bytes(b"xyz")

    class FakeView:
        def set_items(self, items, **kw): pass
        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, s): pass
        def current_cursor_item(self): return None
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, h): pass
        def select_item(self, n): pass

    p = PanePresenter(FakeView(), LocalVFS())
    p._items = [FileItem(name="mydir", path=d, is_dir=True, size=0, modified=0.0)]
    p._marks = {str(d)}

    p._start_dir_size_calc()
    # wait for daemon thread (max 2s)
    deadline = time.time() + 2
    while p._dir_size_result is None and time.time() < deadline:
        time.sleep(0.05)

    assert p._dir_size_result == 3  # "xyz"


# ── DirectoryModel._dir_sizes column ──────────────────────────────────────────

def test_dir_size_calculated(qapp, tmp_path: Path) -> None:
    """set_dir_size caches size and data() reflects it in COL_SIZE."""
    from biome_fm.models.directory_model import DirectoryModel, COL_SIZE
    from biome_fm.models.file_item import FileItem
    from biome_fm.qt import Qt

    d = tmp_path / "mydir"
    d.mkdir()
    item = FileItem(name="mydir", path=d, is_dir=True, size=0, modified=0.0)
    model = DirectoryModel()
    model.set_items([item])
    model.set_dir_size(d, 1024)
    idx = model.index(0, COL_SIZE)
    text = model.data(idx, Qt.ItemDataRole.DisplayRole)
    assert "1.0 KB" == text


def test_file_size_unchanged(qapp, tmp_path: Path) -> None:
    """set_dir_size does not affect file rows."""
    from biome_fm.models.directory_model import DirectoryModel, COL_SIZE
    from biome_fm.models.file_item import FileItem
    from biome_fm.qt import Qt

    f = tmp_path / "readme.txt"
    f.write_bytes(b"x" * 512)
    item = FileItem(name="readme.txt", path=f, is_dir=False, size=512, modified=0.0)
    model = DirectoryModel()
    model.set_items([item])
    # calling set_dir_size on a file path should have no effect
    model.set_dir_size(f, 999)
    idx = model.index(0, COL_SIZE)
    text = model.data(idx, Qt.ItemDataRole.DisplayRole)
    assert text == "512 B"
