"""Integration tests for PaneView (requires Qt, offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.qt import Qt
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
        assert view._path_bar.lineEdit().text() == "/home/user"

    def test_show_error_displays_message(self, view):
        view.show_error("Permission denied")
        assert "Permission denied" in view._path_bar.lineEdit().text()

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
        view._path_bar.lineEdit().setText("/tmp/test")
        view._path_bar.lineEdit().returnPressed.emit()
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


class TestNumericCountPrefix:
    """F288 — Numeric count prefix moves cursor N rows."""

    def test_count_prefix_moves_down_n_rows(self, qtbot, view):
        items = [_item(f"f{i:02d}.txt") for i in range(20)]
        view.set_items(items)
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        view._table._count = "5"
        qtbot.keyClick(view._table, Qt.Key.Key_Down)
        assert view._table.currentIndex().row() == 5

    def test_count_prefix_clamps_to_last_row(self, qtbot, view):
        items = [_item(f"f{i}.txt") for i in range(5)]
        view.set_items(items)
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        view._table._count = "99"
        qtbot.keyClick(view._table, Qt.Key.Key_Down)
        assert view._table.currentIndex().row() == 4  # last row

    def test_digit_key_accumulates_count(self, qtbot, view):
        view.set_items([_item("a.txt"), _item("b.txt")])
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        qtbot.keyClick(view._table, Qt.Key.Key_1)
        qtbot.keyClick(view._table, Qt.Key.Key_2)
        assert view._table._count == "12"

    def test_non_digit_resets_count(self, qtbot, view):
        view.set_items([_item("a.txt")])
        view._table._count = "5"
        qtbot.keyClick(view._table, Qt.Key.Key_Down)
        assert view._table._count == ""


class TestVisualSelectionVMode:
    """F289 — Visual selection V mode."""

    def test_v_key_enters_visual_mode(self, qtbot, view):
        items = [_item("a.txt"), _item("b.txt"), _item("c.txt")]
        view.set_items(items)
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        assert not view._table._v_mode
        qtbot.keyClick(view._table, Qt.Key.Key_V)
        assert view._table._v_mode
        assert view._table._v_anchor is not None

    def test_second_v_exits_visual_mode(self, qtbot, view):
        view.set_items([_item("a.txt"), _item("b.txt")])
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        qtbot.keyClick(view._table, Qt.Key.Key_V)
        assert view._table._v_mode
        qtbot.keyClick(view._table, Qt.Key.Key_V)
        assert not view._table._v_mode

    def test_escape_exits_visual_mode(self, qtbot, view):
        view.set_items([_item("a.txt"), _item("b.txt")])
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        qtbot.keyClick(view._table, Qt.Key.Key_V)
        assert view._table._v_mode
        qtbot.keyClick(view._table, Qt.Key.Key_Escape)
        assert not view._table._v_mode

    def test_v_mode_nav_emits_mark_range(self, qtbot, view):
        items = [_item(f"f{i}.txt") for i in range(5)]
        view.set_items(items)
        view._table.setCurrentIndex(view._proxy.index(0, 0))
        received = []
        view.mark_range_requested.connect(lambda a, b: received.append((a, b)))
        qtbot.keyClick(view._table, Qt.Key.Key_V)
        qtbot.keyClick(view._table, Qt.Key.Key_Down)
        assert len(received) == 1
        assert received[0][0] == view._table._v_anchor
