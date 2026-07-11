"""Integration tests for PaneView (requires Qt, offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(name: str, *, is_dir: bool = False, size: int = 0) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=is_dir, size=size, modified=0.0)


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    v.show()
    return v


class TestPaneView:
    def test_set_items_updates_table_rows(self, view):
        items = [_item("..", is_dir=True), _item("docs", is_dir=True), _item("readme.txt")]
        view.set_items(items)
        assert view._model.rowCount() == 3

    def test_set_path_updates_path_bar(self, view):
        view.set_path(Path("/home/user"))
        assert view._path_bar.text() == "/home/user"

    def test_show_error_displays_message(self, view):
        view.show_error("Permission denied")
        assert "Permission denied" in view._path_bar.text()

    def test_item_activated_signal_on_activation(self, qtbot, view):
        items = [_item("docs", is_dir=True)]
        view.set_items(items)
        received: list[FileItem] = []
        view.item_activated.connect(received.append)
        # activate via model's signal path
        proxy_idx = view._proxy.index(0, 0)
        view._on_activated(proxy_idx)
        assert len(received) == 1
        assert received[0].name == "docs"

    def test_path_change_requested_on_enter(self, qtbot, view):
        received: list[Path] = []
        view.path_change_requested.connect(received.append)
        view._path_bar.setText("/tmp/test")
        view._path_bar.returnPressed.emit()
        assert received == [Path("/tmp/test")]

    def test_selected_items_returns_fileitem_list(self, view):
        items = [_item("alpha.txt", size=10), _item("beta.txt", size=20)]
        view.set_items(items)
        # select first row via table selection model
        idx = view._table.model().index(0, 0)
        view._table.setCurrentIndex(idx)
        view._table.selectRow(0)
        sel = view.selected_items()
        assert len(sel) == 1

    def test_proxy_sorts_dirs_first(self, view):
        items = [
            _item("zebra.txt"),
            _item("alpha", is_dir=True),
            _item("..", is_dir=True),
        ]
        view.set_items(items)
        # proxy should sort: ".." first, then "alpha" (dir), then "zebra.txt"
        first = view._proxy.data(view._proxy.index(0, 0))
        second = view._proxy.data(view._proxy.index(1, 0))
        assert first == ".."
        assert second == "alpha"

    def test_set_status_displays_text(self, view):
        view.set_status("42 items")
        assert view._status_label.text() == "42 items"
