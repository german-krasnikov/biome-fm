"""ContextBar — horizontal row of removable attachment chips."""
from __future__ import annotations

from biome_fm.qt import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    Qt,
    QWidget,
    Signal,
)


class ContextBar(QScrollArea):
    """Horizontal scroll area showing attachment chips. Hidden when empty."""

    chip_removed = Signal(int)  # emits index of removed chip

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(36)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(4)
        self._layout.addStretch()
        self.setWidget(self._container)
        self._chips: list[str] = []
        self.hide()

    def add_chip(self, name: str) -> None:
        self._chips.append(name)
        self._rebuild()

    def clear_chips(self) -> None:
        self._chips.clear()
        self._rebuild()

    def _rebuild(self) -> None:
        while self._layout.count() > 0:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, name in enumerate(self._chips):
            chip = _Chip(name, i, self._container)
            chip.remove_clicked.connect(self._on_remove)
            self._layout.addWidget(chip)
        self._layout.addStretch()
        self.setVisible(bool(self._chips))

    def _on_remove(self, index: int) -> None:
        if 0 <= index < len(self._chips):
            self._chips.pop(index)
            self._rebuild()
            self.chip_removed.emit(index)


class _Chip(QFrame):
    """Single attachment chip: label + X button."""

    remove_clicked = Signal(int)

    def __init__(self, name: str, index: int, parent=None):
        super().__init__(parent)
        self._index = index
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 1, 2, 1)
        layout.setSpacing(2)
        label = QLabel(name)
        label.setStyleSheet("font-size: 11px;")
        btn = QPushButton("x")
        btn.setFixedSize(16, 16)
        btn.setStyleSheet("border:none; font-size:12px; font-weight:bold;")
        btn.clicked.connect(lambda: self.remove_clicked.emit(self._index))
        layout.addWidget(label)
        layout.addWidget(btn)
        self.setStyleSheet(
            "background: #2a2a3a; border: 1px solid #444; border-radius: 4px;"
        )
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
