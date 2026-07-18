"""Unit tests for PanePresenter.toggle_mark_at — Cmd+Click mark toggle."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _make_presenter(items):
    view = MagicMock()
    view.current_cursor_item.return_value = items[0] if items else None
    vfs = MagicMock()
    vfs.list_dir.return_value = items
    p = PanePresenter(view=view, vfs=vfs, opener=lambda _: None)
    p._items = list(items)
    p._cwd = Path("/tmp")
    return p, view


def test_toggle_mark_at_marks_item():
    item = FileItem(name="file.txt", path=Path("/tmp/file.txt"), is_dir=False, size=100, modified=0.0)
    p, view = _make_presenter([item])
    p.toggle_mark_at(item)
    assert item.path in p.marks
    view.set_marked.assert_called()


def test_toggle_mark_at_unmarks_item():
    item = FileItem(name="file.txt", path=Path("/tmp/file.txt"), is_dir=False, size=100, modified=0.0)
    p, view = _make_presenter([item])
    p.toggle_mark_at(item)
    p.toggle_mark_at(item)
    assert item.path not in p.marks


def test_toggle_mark_at_ignores_dotdot():
    item = FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0)
    p, view = _make_presenter([item])
    p.toggle_mark_at(item)
    assert len(p._marks) == 0


def test_toggle_mark_at_does_not_advance_cursor():
    item = FileItem(name="file.txt", path=Path("/tmp/file.txt"), is_dir=False, size=100, modified=0.0)
    p, view = _make_presenter([item])
    p.toggle_mark_at(item)
    view.advance_cursor.assert_not_called()
    view.retreat_cursor.assert_not_called()
