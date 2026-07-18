"""F328 — Selection Operations Performance: _marks uses str keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


HOME = Path("/home/user")


def _item(name: str, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=HOME / name, is_dir=is_dir, size=0, modified=0.0)


class FakeVFS:
    def __init__(self, items: list[FileItem]) -> None:
        self._items = items

    def listdir(self, path: Path) -> list[FileItem]:
        return list(self._items)


@dataclass
class FakePaneView:
    items: list = field(default_factory=list)
    path: Path | None = None
    errors: list = field(default_factory=list)
    status: str = ""
    marked: set = field(default_factory=set)

    def set_items(self, items: list, **kwargs) -> None:
        self.items = list(items)

    def set_path(self, path: Path) -> None:
        self.path = path

    def show_error(self, message: str) -> None:
        self.errors.append(message)

    def set_status(self, text: str) -> None:
        self.status = text

    def set_marked(self, paths: set) -> None:
        self.marked = set(paths)

    cursor: object = None

    def current_cursor_item(self):
        return self.cursor

    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v: bool): pass
    def set_nav_history(self, paths: list): pass
    def select_item(self, name: str): pass
    def set_dir_size(self, path: Path, size: int): pass


class TestSelectionPerf:
    def test_marks_use_str_keys(self):
        from biome_fm.presenters.pane_presenter import PanePresenter

        items = [_item("a.txt"), _item("b.txt")]
        vfs = FakeVFS(items)
        view = FakePaneView(cursor=items[0])
        p = PanePresenter(view=view, vfs=vfs, home=HOME)
        p.navigate_to(HOME)

        p.toggle_mark()

        # _marks should contain str keys
        assert len(p._marks) > 0
        for key in p._marks:
            assert isinstance(key, str), f"Expected str, got {type(key)}"

    def test_push_marks_sends_path_set(self):
        from biome_fm.presenters.pane_presenter import PanePresenter

        items = [_item("x.txt"), _item("y.txt")]
        vfs = FakeVFS(items)
        view = FakePaneView(cursor=items[0])
        p = PanePresenter(view=view, vfs=vfs, home=HOME)
        p.navigate_to(HOME)

        p.toggle_mark()

        # view.set_marked receives a set of Path objects
        for path in view.marked:
            assert isinstance(path, Path), f"Expected Path, got {type(path)}"
