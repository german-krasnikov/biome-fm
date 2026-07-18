"""Unit tests for vi-style scroll motions in _PaneTableView (F292)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(name: str) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=False, size=0, modified=0.0)


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    items = [FileItem("..", Path(".."), True, 0, 0.0)] + [_item(f"file{i:02d}.txt") for i in range(10)]
    v.set_items(items)
    return v


def _key(key, mods=Qt.KeyboardModifier.NoModifier):
    return QKeyEvent(QEvent.Type.KeyPress, key, mods)


def test_G_goes_to_last_row(qtbot, view):
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    ev = _key(Qt.Key.Key_G, Qt.KeyboardModifier.ShiftModifier)
    view._table.keyPressEvent(ev)
    last = view._table.model().rowCount() - 1
    assert view._table.currentIndex().row() == last


def test_gg_goes_to_first_row(qtbot, view):
    # move to last row first
    last = view._table.model().rowCount() - 1
    view._table.setCurrentIndex(view._table.model().index(last, 0))
    # press g twice
    view._table.keyPressEvent(_key(Qt.Key.Key_G))
    assert view._table._g_pending
    view._table.keyPressEvent(_key(Qt.Key.Key_G))
    assert view._table.currentIndex().row() == 0


def test_ctrl_f_page_down(qtbot, view):
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    view._table.keyPressEvent(_key(Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier))
    # should have moved down (row > 0)
    assert view._table.currentIndex().row() > 0


def test_ctrl_b_page_up(qtbot, view):
    last = view._table.model().rowCount() - 1
    view._table.setCurrentIndex(view._table.model().index(last, 0))
    view._table.keyPressEvent(_key(Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier))
    assert view._table.currentIndex().row() < last
