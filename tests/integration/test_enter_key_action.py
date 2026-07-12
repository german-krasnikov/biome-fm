"""Integration tests: Enter key emits item_activated for each item type."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(name, *, is_dir=False):
    return FileItem(name=name, path=Path("/fake") / name, is_dir=is_dir, size=0, modified=0.0)


def _press_enter(table):
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    table.keyPressEvent(ev)


@pytest.fixture
def view(qtbot):
    v = PaneView()
    qtbot.addWidget(v)
    return v


def test_enter_on_file_emits_item_activated(qtbot, view):
    view.set_items([_item("readme.txt")])
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    received = []
    view.item_activated.connect(received.append)
    _press_enter(view._table)
    assert len(received) == 1
    assert received[0].name == "readme.txt"


def test_enter_on_folder_emits_item_activated(qtbot, view):
    view.set_items([_item("docs", is_dir=True)])
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    with qtbot.waitSignal(view.item_activated, timeout=500) as blocker:
        _press_enter(view._table)
    assert blocker.args[0].name == "docs"
    assert blocker.args[0].is_dir


def test_enter_on_dotdot_emits_item_activated(qtbot, view):
    view.set_items([_item("..", is_dir=True), _item("file.txt")])
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    with qtbot.waitSignal(view.item_activated, timeout=500) as blocker:
        _press_enter(view._table)
    assert blocker.args[0].name == ".."


def test_enter_on_archive_emits_item_activated(qtbot, view):
    view.set_items([_item("backup.zip")])
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    with qtbot.waitSignal(view.item_activated, timeout=500) as blocker:
        _press_enter(view._table)
    assert blocker.args[0].name == "backup.zip"


def test_enter_with_no_selection_is_noop(qtbot, view):
    view.set_items([_item("file.txt")])
    view._table.clearSelection()
    view._table.setCurrentIndex(view._table.model().index(-1, 0))
    received = []
    view.item_activated.connect(received.append)
    _press_enter(view._table)
    assert received == []


def test_numpad_enter_also_emits(qtbot, view):
    view.set_items([_item("file.txt")])
    view._table.setCurrentIndex(view._table.model().index(0, 0))
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier)
    with qtbot.waitSignal(view.item_activated, timeout=500):
        view._table.keyPressEvent(ev)


def test_enter_tab_override_still_works(qtbot, view):
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
    result = view._table.event(ev)
    assert result is True
