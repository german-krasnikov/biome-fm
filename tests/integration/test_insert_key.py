"""Integration tests for Insert key — mark + advance with presenter wired."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(name, *, is_dir=False):
    return FileItem(name=name, path=Path(name), is_dir=is_dir, size=0, modified=0.0)


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    items = [_item("..", is_dir=True), _item("a.txt"), _item("b.txt"), _item("c.txt")]
    v.set_items(items)
    v._table.setCurrentIndex(v._table.model().index(1, 0))  # row 1 = a.txt
    # Wire advance_cursor to the signal (simulates presenter.toggle_mark side-effect)
    v.mark_toggle_requested.connect(v.advance_cursor)
    return v


def test_insert_emits_mark_toggle(qtbot, view):
    with qtbot.waitSignal(view.mark_toggle_requested, timeout=500):
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Insert, Qt.KeyboardModifier.NoModifier)
        view._table.keyPressEvent(ev)


def test_insert_advances_cursor(qtbot, view):
    before = view._table.currentIndex().row()  # 1
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Insert, Qt.KeyboardModifier.NoModifier)
    view._table.keyPressEvent(ev)
    assert view._table.currentIndex().row() == before + 1


def test_insert_at_last_row_does_not_overflow(qtbot, view):
    """Insert on last row: signal fires, cursor stays at last row."""
    last_row = view._table.model().rowCount() - 1
    view._table.setCurrentIndex(view._table.model().index(last_row, 0))
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Insert, Qt.KeyboardModifier.NoModifier)
    view._table.keyPressEvent(ev)
    assert view._table.currentIndex().row() == last_row  # advance_cursor clamps at end
