"""JumpBar — type-to-navigate overlay label."""

from __future__ import annotations

from biome_fm.qt import QHBoxLayout, QLabel, QTimer, QWidget, Signal


class JumpBar(QWidget):
    jump_text_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self._label = QLabel()
        self._label.setStyleSheet("background: rgba(0,0,0,0.7); color: white; padding: 2px 6px;")
        layout.addWidget(self._label)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.clear)
        self.hide()

    def append_char(self, char: str) -> None:
        self._text += char
        self._label.setText(self._text)
        self.show()
        self._timer.start(600)
        self.jump_text_changed.emit(self._text)

    def clear(self) -> None:
        self._timer.stop()
        self._text = ""
        self._label.setText("")
        self.hide()
