"""Toolbar Builder dialog — edit the custom toolbar action list."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from biome_fm.commands.registry import CommandRegistry


class ToolbarBuilderDialog(QDialog):
    accepted_actions = Signal(list)  # list[str]

    def __init__(
        self,
        registry: CommandRegistry,
        current: list[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Customize Toolbar")
        self._registry = registry

        self._left = QListWidget()
        for entry in registry.search(""):
            self._left.addItem(entry.name)

        self._right = QListWidget()
        for name in current:
            self._right.addItem(name)

        add_btn = QPushButton("Add →")
        add_btn.clicked.connect(self._add)
        remove_btn = QPushButton("← Remove")
        remove_btn.clicked.connect(self._remove)
        up_btn = QPushButton("Move Up")
        up_btn.clicked.connect(self._move_up)
        down_btn = QPushButton("Move Down")
        down_btn.clicked.connect(self._move_down)

        mid = QVBoxLayout()
        for btn in (add_btn, remove_btn, up_btn, down_btn):
            mid.addWidget(btn)
        mid.addStretch()

        lists = QHBoxLayout()
        lists.addWidget(self._left)
        lists.addLayout(mid)
        lists.addWidget(self._right)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(lists)
        layout.addWidget(buttons)

    def _ok(self) -> None:
        names = [self._right.item(i).text() for i in range(self._right.count())]
        self.accepted_actions.emit(names)
        self.accept()

    def _add(self) -> None:
        item = self._left.currentItem()
        if item:
            self._right.addItem(item.text())

    def _remove(self) -> None:
        row = self._right.currentRow()
        if row >= 0:
            self._right.takeItem(row)

    def _move_up(self) -> None:
        row = self._right.currentRow()
        if row > 0:
            item = self._right.takeItem(row)
            self._right.insertItem(row - 1, item)
            self._right.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        row = self._right.currentRow()
        if row < self._right.count() - 1:
            item = self._right.takeItem(row)
            self._right.insertItem(row + 1, item)
            self._right.setCurrentRow(row + 1)
