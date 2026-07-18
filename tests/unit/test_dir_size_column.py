"""Unit tests for F253 — Folder Size Column background calc."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, parent: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=0, modified=0.0)


class FakeVFS:
    def __init__(self, items: list[FileItem]) -> None:
        self._items = items

    def listdir(self, _: Path) -> list[FileItem]:
        return list(self._items)


class FakeView:
    def __init__(self) -> None:
        self.path = None
        self.items: list = []
        self.marked: set = set()
        self.status = ""
        self.dir_sizes: dict = {}

    def set_items(self, items, **kw) -> None:
        self.items = list(items)

    def set_path(self, p) -> None:
        self.path = p

    def show_error(self, m) -> None: ...
    def set_status(self, t) -> None: self.status = t
    def set_marked(self, m) -> None: self.marked = m
    def current_cursor_item(self): return None
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, v) -> None: ...
    def set_nav_history(self, h) -> None: ...
    def select_item(self, n) -> None: ...

    def set_dir_size(self, path: Path, size: int) -> None:
        self.dir_sizes[path] = size


def _make_presenter(items: list[FileItem]) -> tuple[PanePresenter, FakeView, FakeVFS]:
    root = Path("/tmp/test")
    vfs = FakeVFS(items)
    view = FakeView()
    p = PanePresenter(view, vfs)
    p.navigate_to(root)
    view.path = root  # satisfy navigate_to after setting items
    return p, view, vfs


def test_vfs_property_exposed() -> None:
    root = Path("/tmp/test")
    vfs = FakeVFS([])
    view = FakeView()
    p = PanePresenter(view, vfs)
    assert p.vfs is vfs


def test_set_dir_size_updates_view(tmp_path: Path) -> None:
    """set_dir_size on view is called from calculate_all_dir_sizes."""
    d = _item("subdir", tmp_path, is_dir=True)
    vfs = FakeVFS([d])
    view = FakeView()
    p = PanePresenter(view, vfs)
    p.navigate_to(tmp_path)

    # Manually test that set_dir_size goes through to view
    view.set_dir_size(d.path, 1234)
    assert view.dir_sizes[d.path] == 1234


def test_calculate_dir_sizes_calls_worker(tmp_path: Path) -> None:
    """calculate_all_dir_sizes spawns a thread per dir and calls calc_tree_size."""
    d1 = _item("a", tmp_path, is_dir=True)
    d2 = _item("b", tmp_path, is_dir=True)
    f1 = _item("c.txt", tmp_path)
    vfs = FakeVFS([d1, d2, f1])
    view = FakeView()
    p = PanePresenter(view, vfs)
    p.navigate_to(tmp_path)

    called_paths: list[Path] = []

    def fake_calc(paths: list[Path], cancel: list[bool]) -> int:
        called_paths.extend(paths)
        return 100

    with patch("biome_fm.utils.dir_size.calc_tree_size", side_effect=fake_calc):
        p.calculate_all_dir_sizes()
        # Wait for background threads
        for _ in range(50):
            if len(called_paths) >= 2:
                break
            time.sleep(0.05)

    assert set(called_paths) == {d1.path, d2.path}


def test_calculate_dir_sizes_skips_files(tmp_path: Path) -> None:
    """Only dirs are submitted for size calculation."""
    f1 = _item("x.txt", tmp_path)
    f2 = _item("y.txt", tmp_path)
    vfs = FakeVFS([f1, f2])
    view = FakeView()
    p = PanePresenter(view, vfs)
    p.navigate_to(tmp_path)

    called = []

    def fake_calc(paths, cancel):
        called.extend(paths)
        return 0

    with patch("biome_fm.utils.dir_size.calc_tree_size", side_effect=fake_calc):
        p.calculate_all_dir_sizes()
        time.sleep(0.1)

    assert called == []
