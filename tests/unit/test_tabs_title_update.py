"""TDD: TabsPresenter.on_item_activated must update tab title on dir navigation."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.tabs_presenter import TabsPresenter


def _make_tabs(new_path: Path) -> tuple[TabsPresenter, MagicMock, MagicMock]:
    tabs_view = MagicMock()
    vfs = MagicMock()
    tabs = TabsPresenter(vfs, tabs_view, lambda: MagicMock())

    mock_pane = MagicMock()
    mock_pane.current_path = new_path
    tabs._tabs = [mock_pane]
    tabs._views = [MagicMock()]
    tabs._active_idx = 0
    return tabs, tabs_view, mock_pane


def test_on_item_activated_dir_updates_tab_title():
    new_dir = Path("/foo/bar")
    tabs, tabs_view, mock_pane = _make_tabs(new_dir)

    item = FileItem("bar", new_dir, is_dir=True, size=0, modified=0.0)
    tabs.on_item_activated(item)

    mock_pane.on_item_activated.assert_called_once_with(item)
    tabs_view.set_tab_title.assert_called_once_with(0, "bar")


def test_on_item_activated_updates_tooltip():
    new_dir = Path("/foo/bar")
    tabs, tabs_view, _ = _make_tabs(new_dir)

    item = FileItem("bar", new_dir, is_dir=True, size=0, modified=0.0)
    tabs.on_item_activated(item)

    tabs_view.set_tab_tooltip.assert_called_once_with(0, str(new_dir))


def test_on_item_activated_file_no_path_change():
    """File activation: current_path stays same, title still updated (idempotent)."""
    cur = Path("/foo")
    tabs, tabs_view, mock_pane = _make_tabs(cur)
    mock_pane.current_path = cur  # path doesn't change for file open

    item = FileItem("readme.txt", cur / "readme.txt", is_dir=False, size=100, modified=0.0)
    tabs.on_item_activated(item)

    mock_pane.on_item_activated.assert_called_once_with(item)
    # title updated to current_path.name (same value, but called)
    tabs_view.set_tab_title.assert_called_once_with(0, "foo")
