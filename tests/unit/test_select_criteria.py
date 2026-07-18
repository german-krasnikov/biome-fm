"""Unit tests for SelectCriteria and PanePresenter.select_where (F221)."""
from __future__ import annotations

import time
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.select_criteria import SelectCriteria


def _file(name: str, size: int = 0, modified: float | None = None) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=False, size=size,
                    modified=modified if modified is not None else time.time())


def _dir(name: str) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=True, size=0, modified=time.time())


def test_no_criteria_matches_all() -> None:
    c = SelectCriteria()
    assert c.matches(_file("foo.py"))
    assert c.matches(_file("bar.txt"))


def test_matches_name_glob() -> None:
    c = SelectCriteria(name_glob="*.py")
    assert c.matches(_file("test.py"))
    assert not c.matches(_file("test.txt"))


def test_matches_extension() -> None:
    c = SelectCriteria(extensions=[".py", ".pyi"])
    assert c.matches(_file("mod.py"))
    assert c.matches(_file("types.pyi"))
    assert not c.matches(_file("README.md"))


def test_matches_size_range() -> None:
    c = SelectCriteria(min_size=100, max_size=500)
    assert c.matches(_file("a", size=200))
    assert not c.matches(_file("b", size=50))
    assert not c.matches(_file("c", size=600))


def test_min_size_only() -> None:
    c = SelectCriteria(min_size=100)
    assert c.matches(_file("a", size=100))
    assert c.matches(_file("b", size=9999))
    assert not c.matches(_file("c", size=99))


def test_matches_combined() -> None:
    c = SelectCriteria(name_glob="test_*", extensions=[".py"], min_size=10)
    assert c.matches(_file("test_foo.py", size=100))
    assert not c.matches(_file("foo.py", size=100))     # name_glob fails
    assert not c.matches(_file("test_foo.txt", size=100))  # ext fails
    assert not c.matches(_file("test_foo.py", size=5))  # size fails


def test_dotdot_never_matches() -> None:
    c = SelectCriteria()
    assert not c.matches(FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0))


def test_dirs_match_when_no_criteria() -> None:
    """Dirs should match empty criteria (for consistency with select_all)."""
    c = SelectCriteria()
    assert c.matches(_dir("subdir"))


# ── PanePresenter.select_where ───────────────────────────────────────────────

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


class _FakeView:
    def __init__(self) -> None:
        self.marked: set[Path] = set()
        self.items: list[FileItem] = []
        self.status = ""

    def set_items(self, items, **kw) -> None:
        self.items = items

    def set_path(self, path) -> None: ...
    def show_error(self, msg) -> None: ...
    def set_status(self, text) -> None:
        self.status = text
    def set_marked(self, paths) -> None:
        self.marked = paths
    def current_cursor_item(self) -> FileItem | None: return None
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, v) -> None: ...
    def set_nav_history(self, paths) -> None: ...
    def select_item(self, name) -> None: ...
    def set_dir_size(self, path, size) -> None: ...


class _FakeVFS:
    def __init__(self, items: list[FileItem]) -> None:
        self._items = items

    def listdir(self, path: Path) -> list[FileItem]:
        return list(self._items)


def test_select_where_marks_matching() -> None:
    items = [
        FileItem("foo.py", Path("/d/foo.py"), False, 100, 0.0),
        FileItem("bar.txt", Path("/d/bar.txt"), False, 100, 0.0),
        FileItem("baz.py", Path("/d/baz.py"), False, 100, 0.0),
    ]
    view = _FakeView()
    vfs = _FakeVFS(items)
    p = PanePresenter(view, vfs)
    p.navigate_to(Path("/d"))
    p.select_where(lambda i: i.name.endswith(".py"))
    assert Path("/d/foo.py") in view.marked
    assert Path("/d/baz.py") in view.marked
    assert Path("/d/bar.txt") not in view.marked
