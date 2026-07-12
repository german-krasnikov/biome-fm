"""Integration tests for PaneView key bindings."""
import pytest
from pathlib import Path
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
    v.set_items([_item("..", is_dir=True), _item("a.txt"), _item("b.txt")])
    v._table.setCurrentIndex(v._table.model().index(1, 0))
    return v


def test_space_emits_view_requested(qtbot, view):
    with qtbot.waitSignal(view.view_requested, timeout=500):
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier)
        view._table.keyPressEvent(ev)


def test_shift_down_emits_mark_toggle(qtbot, view):
    with qtbot.waitSignal(view.mark_toggle_requested, timeout=500):
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
        view._table.keyPressEvent(ev)


def test_shift_up_emits_mark_toggle_up(qtbot, view):
    with qtbot.waitSignal(view.mark_toggle_up_requested, timeout=500):
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.ShiftModifier)
        view._table.keyPressEvent(ev)
