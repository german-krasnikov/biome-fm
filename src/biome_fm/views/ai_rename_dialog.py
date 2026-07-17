"""AI Rename Suggestions dialog."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class AIRenameDialog(QDialog):
    rename_requested = Signal(list)  # list of (original, new_name) tuples

    def __init__(
        self,
        names: list[str],
        suggestions: list[str | None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Rename Suggestions")
        layout = QVBoxLayout(self)

        has_suggestions = any(s is not None for s in suggestions)

        self._label = QLabel("No suggestions available.")
        self._label.setVisible(not has_suggestions)
        layout.addWidget(self._label)

        self._table = QTableWidget(len(names), 3)
        self._table.setHorizontalHeaderLabels(["Original", "Suggested", "Apply"])
        self._table.setVisible(has_suggestions)
        layout.addWidget(self._table)

        for i, (name, sug) in enumerate(zip(names, suggestions)):
            self._table.setItem(i, 0, QTableWidgetItem(name))
            self._table.setItem(i, 1, QTableWidgetItem(sug or ""))
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(
                Qt.CheckState.Checked if sug is not None else Qt.CheckState.Unchecked
            )
            self._table.setItem(i, 2, chk)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._names = names
        self._suggestions = suggestions

    def _on_accept(self) -> None:
        pairs = []
        for i, (name, sug) in enumerate(zip(self._names, self._suggestions)):
            chk = self._table.item(i, 2)
            if sug and chk and chk.checkState() == Qt.CheckState.Checked:
                pairs.append((name, sug))
        self.rename_requested.emit(pairs)
        self.accept()
