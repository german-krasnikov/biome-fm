"""PatternDialog — select/deselect files by glob pattern."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class PatternDialog(QDialog):
    """Ask for a glob pattern + select/deselect mode."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select by Pattern")

        self._line = QLineEdit("*")
        self._mode = QComboBox()
        self._mode.addItems(["Select", "Deselect"])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Pattern:", self._line)
        layout.addRow("Mode:", self._mode)
        layout.addRow(buttons)

    def result_values(self) -> tuple[str, str]:
        """Return (pattern, 'select' | 'deselect')."""
        mode = "select" if self._mode.currentIndex() == 0 else "deselect"
        return self._line.text(), mode
