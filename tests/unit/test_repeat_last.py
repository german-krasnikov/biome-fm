"""Unit tests for F269 — Repeat Last Command."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, parent: Path) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=False, size=0, modified=0.0)


@dataclass
class FakePaneView:
    items: list = field(default_factory=list)
    path: Path | None = None
    status: str = ""
    marked: set = field(default_factory=set)

    def set_items(self, items, **kw) -> None: self.items = list(items)
    def set_path(self, p) -> None: self.path = p
    def set_status(self, t) -> None: self.status = t
    def show_error(self, m) -> None: ...
    def set_marked(self, m) -> None: self.marked = m
    def current_cursor_item(self): return None
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, v) -> None: ...
    def set_nav_history(self, h) -> None: ...
    def select_item(self, n) -> None: ...


class FakeVFS:
    def __init__(self, left: Path, right: Path) -> None:
        self._left = left
        self._right = right

    def listdir(self, path: Path) -> list[FileItem]:
        if path == self._left:
            return [_item("a.txt", path), _item("b.txt", path)]
        return []

    def copy(self, s, d) -> None: ...
    def move(self, s, d) -> None: ...
    def delete(self, p) -> None: ...
    def mkdir(self, p) -> None: ...
    def stat(self, p) -> FileItem: ...  # type: ignore[return]


def _make_manager(tmp_path: Path) -> tuple[ManagerPresenter, Path, Path]:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left_root.mkdir()
    right_root.mkdir()
    vfs = FakeVFS(left_root, right_root)
    lv, rv = FakePaneView(), FakePaneView()
    left_p = PanePresenter(lv, vfs)
    right_p = PanePresenter(rv, vfs)
    left_p.navigate_to(left_root)
    right_p.navigate_to(right_root)
    manager = ManagerPresenter(left_p, right_p, vfs, confirm=lambda _: True)
    return manager, left_root, right_root


def test_repeat_none_noop(tmp_path: Path) -> None:
    manager, _, _ = _make_manager(tmp_path)
    items = [_item("x.txt", tmp_path)]
    # No previous op — should not crash
    manager.repeat_last(items)  # must not raise


def test_last_op_updated_on_copy(tmp_path: Path) -> None:
    manager, left, right = _make_manager(tmp_path)
    items = [_item("a.txt", left)]
    ops: list[tuple] = []
    with patch.object(manager, "_start_op", side_effect=lambda s, d, **kw: ops.append(("_start_op", s, d, kw))):
        manager.copy_selected(items)
    assert manager._last_op_kind == "copy"
    assert manager._last_op_dst == right


def test_last_op_updated_on_move(tmp_path: Path) -> None:
    manager, left, right = _make_manager(tmp_path)
    items = [_item("a.txt", left)]
    with patch.object(manager, "_start_op"):
        manager.move_selected(items)
    assert manager._last_op_kind == "move"
    assert manager._last_op_dst == right


def test_last_op_updated_on_delete(tmp_path: Path) -> None:
    manager, left, _ = _make_manager(tmp_path)
    items = [_item("a.txt", left)]
    with patch.object(manager, "_run"):
        manager.delete_selected(items)
    assert manager._last_op_kind == "delete"
    assert manager._last_op_dst is None


def test_repeat_copy(tmp_path: Path) -> None:
    manager, left, right = _make_manager(tmp_path)
    first_items = [_item("a.txt", left)]
    # Record first copy
    with patch.object(manager, "_start_op") as mock_op:
        manager.copy_selected(first_items)

    # Repeat with different items → same dst
    second_items = [_item("b.txt", left)]
    with patch.object(manager, "_start_op") as mock_op:
        manager.repeat_last(second_items)
        mock_op.assert_called_once_with([second_items[0].path], right, move=False)


def test_repeat_delete(tmp_path: Path) -> None:
    manager, left, _ = _make_manager(tmp_path)
    items = [_item("a.txt", left)]
    with patch.object(manager, "_run"):
        manager.delete_selected(items)

    new_items = [_item("b.txt", left)]
    with patch.object(manager, "delete_selected") as mock_del:
        manager.repeat_last(new_items)
        mock_del.assert_called_once_with(new_items)
