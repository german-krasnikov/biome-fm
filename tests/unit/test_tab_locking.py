"""TDD: Tab locking — no Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.tabs_presenter import TabsPresenter


class _FakeTabsView:
    def __init__(self) -> None:
        self.tabs: list[str] = []
        self.active: int = 0
        self.titles: dict[int, str] = {}

    def add_tab(self, title: str) -> int:
        self.tabs.append(title)
        return len(self.tabs) - 1

    def remove_tab(self, idx: int) -> None:
        self.tabs.pop(idx)

    def set_active_tab(self, idx: int) -> None:
        self.active = idx

    def set_tab_title(self, idx: int, title: str) -> None:
        self.titles[idx] = title

    def set_tab_tooltip(self, idx: int, tooltip: str) -> None:
        pass

    def set_tab_locked(self, idx: int, locked: bool) -> None:
        pass


@dataclass
class _FakePaneView:
    items: list = field(default_factory=list)
    path_text: str = ""
    error: str = ""
    status_text: str = ""
    marked_paths: set = field(default_factory=set)

    def set_items(self, items: list, **kwargs) -> None:
        self.items = items

    def set_path(self, path: Path) -> None:
        self.path_text = str(path)

    def show_error(self, msg: str) -> None:
        self.error = msg

    def set_status(self, text: str) -> None:
        self.status_text = text

    def set_marked(self, paths: set) -> None:
        self.marked_paths = paths

    def current_cursor_item(self) -> FileItem | None:
        return None

    def advance_cursor(self) -> None:
        pass

    def retreat_cursor(self) -> None:
        pass

    def set_filter_visible(self, visible: bool) -> None:
        pass

    def set_nav_history(self, paths: list) -> None:
        pass

    def select_item(self, name: str) -> None:
        pass


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    return tmp_path


def make_presenter(vfs: LocalVFS) -> tuple[TabsPresenter, _FakeTabsView]:
    tv = _FakeTabsView()

    def view_factory() -> _FakePaneView:
        return _FakePaneView()

    tp = TabsPresenter(vfs=vfs, tabs_view=tv, view_factory=view_factory)
    return tp, tv


def test_locked_tab_redirects_to_new_tab(root: Path) -> None:
    vfs = LocalVFS()
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.lock_tab(0)
    tp.navigate_to(root / "dir2")
    assert tp.tab_count == 2
    assert tp.current_path == root / "dir2"


def test_unlock_restores_navigate(root: Path) -> None:
    vfs = LocalVFS()
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.lock_tab(0)
    tp.unlock_tab(0)
    tp.navigate_to(root / "dir2")
    assert tp.tab_count == 1
    assert tp.current_path == root / "dir2"


def test_close_locked_tab_prevented(root: Path) -> None:
    vfs = LocalVFS()
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    tp.lock_tab(0)
    tp.close_tab(0)
    assert tp.tab_count == 2


def test_is_locked(root: Path) -> None:
    vfs = LocalVFS()
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    assert not tp.is_locked(0)
    tp.lock_tab(0)
    assert tp.is_locked(0)
    tp.unlock_tab(0)
    assert not tp.is_locked(0)
