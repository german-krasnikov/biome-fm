"""Unit tests for TabsPresenter.duplicate_tab (F215)."""
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


@dataclass
class _FakePaneView:
    items: list = field(default_factory=list)
    path_text: str = ""

    def set_items(self, items, **kwargs) -> None: self.items = items
    def set_path(self, p: Path) -> None: self.path_text = str(p)
    def set_status(self, t: str) -> None: ...
    def show_error(self, m: str) -> None: ...
    def set_marked(self, paths: set) -> None: ...
    def current_cursor_item(self): return None
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, visible: bool) -> None: ...
    def set_nav_history(self, paths: list) -> None: ...
    def select_item(self, name: str) -> None: ...


def make_presenter(root: Path):
    tv = _FakeTabsView()
    views: list[_FakePaneView] = []

    def view_factory():
        v = _FakePaneView()
        views.append(v)
        return v

    tp = TabsPresenter(vfs=LocalVFS(), tabs_view=tv, view_factory=view_factory)
    tp.new_tab(root)
    return tp, tv


def test_duplicate_tab_creates_new_tab(tmp_path):
    tp, _ = make_presenter(tmp_path)
    assert tp.tab_count == 1
    tp.duplicate_tab(0)
    assert tp.tab_count == 2


def test_duplicate_tab_same_path(tmp_path):
    tp, _ = make_presenter(tmp_path)
    original_path = tp.current_path
    tp.duplicate_tab(0)
    assert tp.presenter_at(1).current_path == original_path
