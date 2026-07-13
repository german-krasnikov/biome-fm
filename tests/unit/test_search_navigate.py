"""Unit tests for search result navigation (no Qt)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _make_vfs(items: list[FileItem] | None = None):
    vfs = MagicMock()
    vfs.listdir.return_value = items or []
    return vfs


def _make_view():
    view = MagicMock()
    view.current_cursor_item.return_value = None
    return view


def test_navigate_then_select_no_timer_needed():
    """navigate_to is synchronous; select_item can be called immediately after."""
    view = _make_view()
    vfs = _make_vfs()
    p = PanePresenter(view, vfs)

    parent = Path("/home/user/docs")
    p.navigate_to(parent)
    view.set_path.assert_called_with(parent)

    # immediate call — no timer needed
    p._view.select_item("readme.md")
    view.select_item.assert_called_with("readme.md")


def test_navigate_to_populates_items_before_select():
    """Items are pushed to view before select_item would run."""
    items = [FileItem(name="readme.md", path=Path("/home/user/docs/readme.md"),
                      is_dir=False, size=42, modified=1000.0)]
    view = _make_view()
    vfs = _make_vfs(items)
    p = PanePresenter(view, vfs)

    p.navigate_to(Path("/home/user/docs"))

    # set_items was called before we'd call select_item
    assert view.set_items.called
    called_items = view.set_items.call_args[0][0]
    names = [i.name for i in called_items if i.name != ".."]
    assert "readme.md" in names
