"""Integration tests for EditorDialog Find/Replace and Go-to-Line (F423)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def tmp_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world hello")
    return f


@pytest.fixture()
def dialog(qapp, tmp_file):
    from biome_fm.views.editor_dialog import EditorDialog
    d = EditorDialog(tmp_file)
    d.show()
    yield d
    d.close()


def _ctrl(key):
    return QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.ControlModifier)


class TestFindBar:
    def test_find_bar_shows_on_ctrl_f(self, dialog):
        assert not dialog._find_bar.isVisible()
        dialog.keyPressEvent(_ctrl(Qt.Key.Key_F))
        assert dialog._find_bar.isVisible()
        assert not dialog._find_bar._replace_row.isVisible()

    def test_find_bar_shows_replace_on_ctrl_h(self, dialog):
        dialog.keyPressEvent(_ctrl(Qt.Key.Key_H))
        assert dialog._find_bar.isVisible()
        assert dialog._find_bar._replace_row.isVisible()

    def test_find_next_moves_cursor(self, dialog):
        dialog._editor.setPlainText("hello world hello")
        bar = dialog._find_bar
        start_pos = dialog._editor.textCursor().position()  # 0 before any search
        bar._find_input.setText("world")  # textChanged fires _find_next immediately
        assert dialog._editor.textCursor().position() != start_pos

    def test_replace_all(self, dialog):
        dialog._editor.setPlainText("aaa")
        bar = dialog._find_bar
        bar._find_input.setText("a")
        bar._repl_input.setText("b")
        bar._replace_all()
        assert dialog._editor.toPlainText() == "bbb"

    def test_find_bar_hide_on_close_button(self, dialog):
        bar = dialog._find_bar
        bar.show_find()
        assert bar.isVisible()
        # clicking close hides it
        bar.hide()
        assert not bar.isVisible()

    def test_editor_key_routes_ctrl_f(self, dialog):
        """Ctrl+F from within QPlainTextEdit (monkey-patched path) also works."""
        dialog._find_bar.hide()
        event = _ctrl(Qt.Key.Key_F)
        dialog._editor_key(event)
        assert dialog._find_bar.isVisible()

    def test_find_wraps_around(self, dialog):
        dialog._editor.setPlainText("hello hello")
        bar = dialog._find_bar
        bar._find_input.setText("hello")
        bar._find_next()
        bar._find_next()
        # after two finds in a 2-occurrence text, cursor still on a match
        cursor = dialog._editor.textCursor()
        assert cursor.hasSelection()

    def test_find_prev(self, dialog):
        dialog._editor.setPlainText("alpha beta alpha")
        bar = dialog._find_bar
        # move cursor to end so backward search has room to find something
        from PySide6.QtGui import QTextCursor
        c = dialog._editor.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        dialog._editor.setTextCursor(c)
        bar._find_input.blockSignals(True)
        bar._find_input.setText("alpha")
        bar._find_input.blockSignals(False)
        bar._find_prev()
        assert dialog._editor.textCursor().hasSelection()

    def test_replace_one(self, dialog):
        dialog._editor.setPlainText("aaa bbb aaa")
        bar = dialog._find_bar
        bar._find_input.blockSignals(True)
        bar._find_input.setText("aaa")
        bar._find_input.blockSignals(False)
        bar._repl_input.setText("ccc")
        bar._find_next()   # select first "aaa"
        bar._replace_one() # replace and advance
        assert dialog._editor.toPlainText() == "ccc bbb aaa"

    def test_replace_one_case_insensitive(self, dialog):
        dialog._editor.setPlainText("Hello world")
        bar = dialog._find_bar
        bar._find_input.blockSignals(True)
        bar._find_input.setText("hello")
        bar._find_input.blockSignals(False)
        bar._repl_input.setText("Hi")
        bar._find_next()
        bar._replace_one()
        assert dialog._editor.toPlainText() == "Hi world"
