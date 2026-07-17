"""Unit tests for persistent filter state — no Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.view_state import ViewState
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, parent: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=0, modified=0.0)


HOME = Path("/home/user")
DOCS = Path("/home/user/docs")


class FakeVFS:
    def __init__(self) -> None:
        self._tree = {
            HOME: [_item("docs", HOME, is_dir=True)],
            DOCS: [_item("readme.txt", DOCS)],
        }

    def listdir(self, path: Path) -> list[FileItem]:
        if path not in self._tree:
            raise FileNotFoundError(path)
        return list(self._tree[path])

    def copy(self, s, d): ...
    def move(self, s, d): ...
    def delete(self, p): ...
    def mkdir(self, p): ...
    def stat(self, p): ...


@dataclass
class FakeView:
    items: list = field(default_factory=list)
    path: Path | None = None
    status: str = ""
    marked: set = field(default_factory=set)
    cursor: FileItem | None = None
    nav_history: list = field(default_factory=list)
    selected: str | None = None
    filter_visible: bool = False
    filter_text: str = ""
    _view_state: ViewState | None = None

    def set_items(self, items, **kw): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): ...
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = paths
    def current_cursor_item(self): return self.cursor
    def advance_cursor(self): ...
    def retreat_cursor(self): ...
    def set_nav_history(self, paths): self.nav_history = paths
    def select_item(self, name): self.selected = name

    def set_filter_visible(self, visible: bool) -> None:
        self.filter_visible = visible

    def set_filter_text(self, text: str) -> None:
        self.filter_text = text

    def get_view_state(self) -> ViewState:
        return self._view_state or ViewState()

    def set_view_state(self, state: ViewState) -> None:
        self._view_state = state
        if state.filter:
            self.set_filter_visible(True)
            self.set_filter_text(state.filter)
        else:
            self.set_filter_visible(False)
            self.set_filter_text("")


def test_filter_saved_on_navigate_away():
    """When navigating away from HOME while filter is active, filter saved in state."""
    view = FakeView()
    view._view_state = ViewState(filter="*.py")
    p = PanePresenter(view=view, vfs=FakeVFS())
    p.navigate_to(HOME)
    # Navigate away — state (including filter) should be saved for HOME
    p.navigate_to(DOCS)
    saved = p._dir_view_state.get(HOME)
    assert saved is not None
    assert saved.filter == "*.py"


def test_filter_restored_on_navigate_back():
    """When navigating back to a directory, its filter is restored."""
    view = FakeView()
    p = PanePresenter(view=view, vfs=FakeVFS())
    p.navigate_to(HOME)
    # Simulate filter being set while at HOME
    view._view_state = ViewState(filter="*.py")
    # Navigate away
    p.navigate_to(DOCS)
    # Reset view state tracker
    view._view_state = ViewState()
    view.filter_text = ""
    view.filter_visible = False
    # Navigate back to HOME — filter should be restored
    p.navigate_to(HOME)
    assert view.filter_text == "*.py"
    assert view.filter_visible is True
