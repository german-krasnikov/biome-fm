"""Unit tests for F241 — persistent filter via DirStateStore. No Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from biome_fm.models.dir_state_store import DirStateStore
from biome_fm.models.file_item import FileItem
from biome_fm.models.view_state import ViewState
from biome_fm.presenters.pane_presenter import PanePresenter


HOME = Path("/home/user")
DOCS = Path("/home/user/docs")


def _item(name: str, parent: Path, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=0, modified=0.0)


class FakeVFS:
    def listdir(self, path: Path) -> list[FileItem]:
        if path == HOME:
            return [_item("docs", HOME, is_dir=True), _item("readme.txt", HOME)]
        if path == DOCS:
            return [_item("file.py", DOCS)]
        raise FileNotFoundError(path)

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
    nav_history: list = field(default_factory=list)
    selected: str | None = None
    filter_visible: bool = False
    filter_text: str = ""
    _state: ViewState | None = None

    def set_items(self, items, **kw): self.items = list(items)
    def set_path(self, path): self.path = path
    def show_error(self, msg): ...
    def set_status(self, text): self.status = text
    def set_marked(self, paths): self.marked = paths
    def current_cursor_item(self): return None
    def advance_cursor(self): ...
    def retreat_cursor(self): ...
    def set_nav_history(self, paths): self.nav_history = paths
    def select_item(self, name): self.selected = name
    def set_filter_visible(self, visible: bool) -> None: self.filter_visible = visible
    def set_filter_text(self, text: str) -> None: self.filter_text = text
    def get_view_state(self) -> ViewState: return self._state or ViewState()
    def set_dir_size(self, path, size): ...

    def set_view_state(self, state: ViewState) -> None:
        self._state = state
        if state.filter:
            self.filter_visible = True
            self.filter_text = state.filter
        else:
            self.filter_visible = False
            self.filter_text = ""


def test_filter_restored_on_navigate(tmp_path: Path) -> None:
    """Filter saved in DirStateStore is restored when navigating to a directory."""
    store = DirStateStore(tmp_path / "state.json")
    store.save(HOME, ViewState(filter="*.py"))

    view = FakeView()
    p = PanePresenter(view=view, vfs=FakeVFS(), store=store)
    p.navigate_to(HOME)

    assert view.filter_visible is True
    assert view.filter_text == "*.py"


def test_no_filter_state_leaves_filter_hidden(tmp_path: Path) -> None:
    """When no saved state exists, filter stays hidden."""
    store = DirStateStore(tmp_path / "state.json")
    view = FakeView()
    p = PanePresenter(view=view, vfs=FakeVFS(), store=store)
    p.navigate_to(HOME)
    assert view.filter_visible is False
