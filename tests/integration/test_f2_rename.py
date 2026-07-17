"""Integration tests: F2 inline rename in PaneView."""
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractItemView, QApplication, QLineEdit

from biome_fm.models.file_item import FileItem
from biome_fm.views.pane_view import PaneView


def _item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=is_dir, size=0, modified=0.0)


def _make_pane(qtbot, items):
    pane = PaneView()
    qtbot.addWidget(pane)
    pane.show()
    pane._model.set_items(items)
    idx = pane._proxy.index(0, 0)
    pane._table.setCurrentIndex(idx)
    qtbot.waitExposed(pane)
    return pane


def test_f2_starts_editing(qtbot):
    """F2 on a valid item must open an inline editor."""
    pane = _make_pane(qtbot, [_item("report.pdf")])
    qtbot.keyPress(pane._table, Qt.Key.Key_F2)
    QApplication.processEvents()
    assert pane._table.state() == QAbstractItemView.State.EditingState


def test_f2_emits_inline_rename_requested(qtbot):
    """Committing the editor emits inline_rename_requested with new name."""
    pane = _make_pane(qtbot, [_item("doc.txt")])

    signals = []
    pane.inline_rename_requested.connect(lambda i, n: signals.append((i, n)))

    qtbot.keyPress(pane._table, Qt.Key.Key_F2)
    QApplication.processEvents()
    editor = QApplication.focusWidget()
    assert isinstance(editor, QLineEdit), f"Expected QLineEdit editor, got {type(editor)}"

    editor.setText("renamed.txt")
    # Commit via delegate directly (qtbot.keyPress on the editor doesn't flush signals)
    delegate = pane._table.itemDelegate()
    delegate.setModelData(editor, pane._proxy, pane._proxy.index(0, 0))

    assert len(signals) == 1
    assert signals[0][1] == "renamed.txt"


def test_f2_escape_cancels_without_signal(qtbot):
    """Pressing Escape in the editor must not emit inline_rename_requested."""
    pane = _make_pane(qtbot, [_item("keep.txt")])

    signals = []
    pane.inline_rename_requested.connect(lambda i, n: signals.append((i, n)))

    qtbot.keyPress(pane._table, Qt.Key.Key_F2)
    QApplication.processEvents()
    editor = QApplication.focusWidget()
    assert isinstance(editor, QLineEdit)

    qtbot.keyPress(editor, Qt.Key.Key_Escape)
    assert signals == []
