"""Unit tests for bookmark file navigation. No Qt."""
from pathlib import Path
from unittest.mock import MagicMock


def _navigate_bookmark(tabs, path: Path) -> None:
    """Mirror of the closure in app.py:_wire_bm._on_bm."""
    target = path if path.is_dir() else path.parent
    tabs.navigate_to(target)
    if not path.is_dir():
        v = tabs.view_at(tabs.active_idx)
        if hasattr(v, "select_item"):
            v.select_item(path.name)


def _make_tabs():
    tabs = MagicMock()
    tabs.active_idx = 0
    view = MagicMock()
    view.select_item = MagicMock()
    tabs.view_at.return_value = view
    return tabs, view


def test_file_bookmark_navigates_to_parent(tmp_path):
    f = tmp_path / "report.pdf"
    f.write_text("x")
    tabs, view = _make_tabs()
    _navigate_bookmark(tabs, f)
    tabs.navigate_to.assert_called_once_with(tmp_path)
    view.select_item.assert_called_once_with("report.pdf")


def test_dir_bookmark_navigates_directly(tmp_path):
    tabs, view = _make_tabs()
    _navigate_bookmark(tabs, tmp_path)
    tabs.navigate_to.assert_called_once_with(tmp_path)
    view.select_item.assert_not_called()


def test_nonexistent_file_goes_to_parent(tmp_path):
    f = tmp_path / "gone.txt"  # doesn't exist
    tabs, view = _make_tabs()
    _navigate_bookmark(tabs, f)
    tabs.navigate_to.assert_called_once_with(tmp_path)
    view.select_item.assert_called_once_with("gone.txt")


def test_file_bookmark_selects_item(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b")
    tabs, view = _make_tabs()
    _navigate_bookmark(tabs, f)
    view.select_item.assert_called_once_with("data.csv")
