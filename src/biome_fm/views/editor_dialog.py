"""EditorDialog — built-in plain-text editor with Ctrl+S save (Feature #18)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout, QWidget

from biome_fm.presenters.editor_presenter import EditorPresenter
from biome_fm.views.editor_highlighter import PygmentsHighlighter


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

        self._presenter = EditorPresenter(self._editor, path)
        self._highlighter = PygmentsHighlighter(self._editor.document(), path.name)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self._save()
                return
            if event.key() == Qt.Key_W:
                self.close()
                return
        super().keyPressEvent(event)

    def _editor_key(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.ControlModifier and event.key() in (Qt.Key_S, Qt.Key_W):
            self.keyPressEvent(event)
        else:
            QPlainTextEdit.keyPressEvent(self._editor, event)

    def _save(self) -> None:
        self._presenter.save()
        self.saved.emit(self._path)
