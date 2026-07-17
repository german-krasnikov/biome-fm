"""Dialog for editing file highlight color rules."""
from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from biome_fm.qt import (
    QColor,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HighlightRulesDialog(QDialog):
    def __init__(
        self,
        rules: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Highlight Rules")
        self.resize(400, 300)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Pattern", "Color"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        for rule in rules:
            self._add_row(rule.get("pattern", ""), rule.get("color", "#ffffff"))

        self._btn_add = QPushButton("Add")
        self._btn_remove = QPushButton("Remove")
        self._btn_add.clicked.connect(self._add_empty_row)
        self._btn_remove.clicked.connect(self._remove_selected)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        btn_row.addStretch()

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addLayout(btn_row)
        layout.addWidget(box)

    def _add_row(self, pattern: str, color: str) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(pattern))
        color_item = QTableWidgetItem(color)
        color_item.setBackground(QColor(color))
        self._table.setItem(row, 1, color_item)

    def _add_empty_row(self) -> None:
        self._add_row("*", "#ffffff")

    def _remove_selected(self) -> None:
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for row in rows:
            self._table.removeRow(row)

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col != 1:
            return
        from PySide6.QtWidgets import QColorDialog
        item = self._table.item(row, 1)
        current = QColor(item.text()) if item else QColor("#ffffff")
        color = QColorDialog.getColor(current, self)
        if color.isValid():
            item.setText(color.name())
            item.setBackground(color)

    def rules(self) -> list[dict]:
        result = []
        for row in range(self._table.rowCount()):
            p = self._table.item(row, 0)
            c = self._table.item(row, 1)
            if p and c and p.text().strip():
                result.append({"pattern": p.text().strip(), "color": c.text()})
        return result

    @classmethod
    def get_rules(
        cls, current_rules: list[dict], parent: QWidget | None = None
    ) -> list[dict] | None:
        dlg = cls(current_rules, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.rules()
        return None
