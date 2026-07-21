"""EditorDialog — built-in plain-text editor with Ctrl+S save (Feature #18)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from biome_fm.presenters.editor_presenter import EditorPresenter
from biome_fm.views.editor_highlighter import PygmentsHighlighter


class _FindBar(QWidget):
    def __init__(self, editor: QPlainTextEdit, parent: QWidget) -> None:
        super().__init__(parent)
        self._editor = editor
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(2)

        # find row
        find_row = QHBoxLayout()
        self._find_input = QLineEdit(placeholderText="Find…")
        self._find_input.returnPressed.connect(self._find_next)
        self._find_input.textChanged.connect(self._find_next)
        find_row.addWidget(QLabel("Find:"))
        find_row.addWidget(self._find_input)
        btn_prev = QPushButton("▲")
        btn_prev.setFixedWidth(28)
        btn_prev.clicked.connect(self._find_prev)
        btn_next = QPushButton("▼")
        btn_next.setFixedWidth(28)
        btn_next.clicked.connect(self._find_next)
        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(28)
        btn_close.clicked.connect(self.hide)
        find_row.addWidget(btn_prev)
        find_row.addWidget(btn_next)
        find_row.addWidget(btn_close)
        lay.addLayout(find_row)

        # replace row (hidden by default)
        self._replace_row = QWidget()
        repl_lay = QHBoxLayout(self._replace_row)
        repl_lay.setContentsMargins(0, 0, 0, 0)
        self._repl_input = QLineEdit(placeholderText="Replace with…")
        repl_lay.addWidget(QLabel("Replace:"))
        repl_lay.addWidget(self._repl_input)
        btn_repl = QPushButton("Replace")
        btn_repl.clicked.connect(self._replace_one)
        btn_repl_all = QPushButton("All")
        btn_repl_all.clicked.connect(self._replace_all)
        repl_lay.addWidget(btn_repl)
        repl_lay.addWidget(btn_repl_all)
        lay.addWidget(self._replace_row)

        self.hide()

    def show_find(self) -> None:
        self._replace_row.hide()
        self.show()
        self._find_input.setFocus()
        self._find_input.selectAll()

    def show_replace(self) -> None:
        self._replace_row.show()
        self.show()
        self._find_input.setFocus()
        self._find_input.selectAll()

    def _find_next(self) -> None:
        term = self._find_input.text()
        if not term:
            return
        if not self._editor.find(term):
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            self._editor.find(term)

    def _find_prev(self) -> None:
        term = self._find_input.text()
        if term:
            self._editor.find(term, QTextDocument.FindFlag.FindBackward)

    def _replace_one(self) -> None:
        c = self._editor.textCursor()
        if c.hasSelection() and c.selectedText().lower() == self._find_input.text().lower():
            c.insertText(self._repl_input.text())
        self._find_next()

    def _replace_all(self) -> None:
        text = self._editor.toPlainText()
        new_text = text.replace(self._find_input.text(), self._repl_input.text())
        if new_text != text:
            c = self._editor.textCursor()
            c.select(QTextCursor.SelectionType.Document)
            c.insertText(new_text)


_EDITOR_INTERCEPT = {Qt.Key.Key_S, Qt.Key.Key_W, Qt.Key.Key_F, Qt.Key.Key_H, Qt.Key.Key_G}


class EditorDialog(QDialog):
    saved = Signal(Path)

    def __init__(self, path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = path
        self.setWindowTitle(path.name)
        self.resize(900, 650)

        self._editor = QPlainTextEdit()
        self._editor.setPlainText(path.read_text(errors="replace") if path.exists() else "")
        self._editor.keyPressEvent = self._editor_key  # type: ignore[method-assign]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._editor)

        self._find_bar = _FindBar(self._editor, self)
        layout.addWidget(self._find_bar)

        self._presenter = EditorPresenter(self._editor, path)
        self._highlighter = PygmentsHighlighter(self._editor.document(), path.name)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            if key == Qt.Key.Key_S:
                self._save()
                return
            if key == Qt.Key.Key_W:
                self.close()
                return
            if key == Qt.Key.Key_F:
                self._find_bar.show_find()
                return
            if key == Qt.Key.Key_H:
                self._find_bar.show_replace()
                return
            if key == Qt.Key.Key_G:
                self._goto_line()
                return
        super().keyPressEvent(event)

    def _editor_key(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() in _EDITOR_INTERCEPT:
            self.keyPressEvent(event)
        else:
            QPlainTextEdit.keyPressEvent(self._editor, event)

    def _save(self) -> None:
        self._presenter.save()
        self.saved.emit(self._path)

    def _goto_line(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        line, ok = QInputDialog.getInt(
            self, "Go to Line", "Line:", min=1, max=self._editor.blockCount()
        )
        if ok:
            cursor = self._editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.NextBlock,
                QTextCursor.MoveMode.MoveAnchor,
                line - 1,
            )
            self._editor.setTextCursor(cursor)
