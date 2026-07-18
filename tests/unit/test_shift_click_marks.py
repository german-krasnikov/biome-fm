"""Unit tests for F266 — Shift+Click range marks."""
from __future__ import annotations

from pathlib import Path

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
        self.marked: set[Path] = set()
        self._cursor: FileItem | None = None

    def set_items(self, items, **kw) -> None: ...
    def set_path(self, p) -> None: ...
    def show_error(self, m) -> None: ...
    def set_status(self, t) -> None: ...
    def set_marked(self, m: set) -> None: self.marked = set(m)
    def current_cursor_item(self): return self._cursor
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, v) -> None: ...
    def set_nav_history(self, h) -> None: ...
    def select_item(self, n) -> None: ...


def _setup(root: Path) -> tuple[PanePresenter, FakeView]:
    items = [_item(f"item_{i}.txt", root) for i in range(5)]
    vfs = FakeVFS(items)
    view = FakeView()
    p = PanePresenter(view, vfs)
    p.navigate_to(root)
    return p, view


def test_mark_range_marks_contiguous_slice(tmp_path: Path) -> None:
    p, view = _setup(tmp_path)
    items = p._items  # [item_0..item_4] (no dotdot after navigate)
    anchor = items[1].path
    target = items[3].path
    p.mark_range(anchor, target)
    expected = {items[1].path, items[2].path, items[3].path}
    assert view.marked == expected


def test_mark_range_reverse_order(tmp_path: Path) -> None:
    p, view = _setup(tmp_path)
    items = p._items
    # anchor=3, target=1 → same range as forward
    p.mark_range(items[3].path, items[1].path)
    expected = {items[1].path, items[2].path, items[3].path}
    assert view.marked == expected


def test_mark_range_skips_dotdot(tmp_path: Path) -> None:
    """mark_range with anchor/target that don't exist → no crash, no marks."""
    p, view = _setup(tmp_path)
    p.mark_range(Path("/nonexistent/a"), Path("/nonexistent/b"))
    assert view.marked == set()


def test_mark_range_adds_to_existing_marks(tmp_path: Path) -> None:
    p, view = _setup(tmp_path)
    items = p._items
    # pre-mark item_0
    p.toggle_mark_at(items[0])
    p.mark_range(items[2].path, items[4].path)
    assert items[0].path in view.marked  # kept
    assert items[2].path in view.marked
    assert items[3].path in view.marked
    assert items[4].path in view.marked
