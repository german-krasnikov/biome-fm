"""Unit tests for Insert key — mark toggle + cursor advance in _PaneTableView."""
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
    return v


def test_insert_emits_mark_toggle_requested(qtbot, view):
    with qtbot.waitSignal(view.mark_toggle_requested, timeout=500):
        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Insert, Qt.KeyboardModifier.NoModifier)
        view._table.keyPressEvent(ev)


def test_insert_advances_cursor(qtbot, view):
    """mark_toggle_requested wired to advance_cursor — simulates presenter behavior."""
    view.mark_toggle_requested.connect(view.advance_cursor)
    before = view._table.currentIndex().row()  # 1
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Insert, Qt.KeyboardModifier.NoModifier)
    view._table.keyPressEvent(ev)
    after = view._table.currentIndex().row()
    assert after == before + 1
