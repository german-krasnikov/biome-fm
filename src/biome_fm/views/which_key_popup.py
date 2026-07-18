"""WhichKeyPopup — floating hint overlay for leader key sequences."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class WhichKeyPopup(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.ToolTip)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self._label = QLabel(self)
        font = self._label.font()
        font.setFamily("monospace")
        self._label.setFont(font)
        layout.addWidget(self._label)
        p = self.palette()
        bg = p.color(p.ColorRole.ToolTipBase).name()
        fg = p.color(p.ColorRole.ToolTipText).name()
        self.setStyleSheet(f"background: {bg}; color: {fg}; border-radius: 4px;")
        self.hide()

    def show_hints(self, hints: list[tuple[str, str]], parent: QWidget | None) -> None:
        if not hints:
            self.hide()
            return
        self._label.setText("  ".join(f"{key} → {seq}" for key, seq in hints))
        self.adjustSize()
        if parent is not None:
            g = parent.mapToGlobal(parent.rect().bottomLeft())
            self.move(g)
        self.show()

    def hide_popup(self) -> None:
        self.hide()
