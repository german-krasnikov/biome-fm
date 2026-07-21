"""Dry-run preview dialog — shows cmd.preview() before executing."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QListWidget, QVBoxLayout,
)

from biome_fm.commands.base import Command, CommandHistory


class DryRunDialog(QDialog):
    def __init__(self, cmd: Command, history: CommandHistory, parent=None) -> None:
        super().__init__(parent)
        self._cmd = cmd
        self._history = history
        self.setWindowTitle("Preview Operation")
        self.resize(500, 300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(cmd.description))
        self._list = QListWidget(self)
        for line in cmd.preview():
            self._list.addItem(line)
        layout.addWidget(self._list)
        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self._run)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _run(self) -> None:
        self._history.execute(self._cmd)
        self.accept()
