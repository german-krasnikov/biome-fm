"""S3 Object Versions browser dialog."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)


class S3VersionsDialog(QDialog):
    restore_requested = Signal(str)  # version_id

    def __init__(self, path: Path, versions: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Versions: {path.name}")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Object: {path}"))
        self._table = QTableWidget(len(versions), 4, self)
        self._table.setHorizontalHeaderLabels(["Version ID", "Last Modified", "Size", "Latest"])
        for row, v in enumerate(versions):
            self._table.setItem(row, 0, QTableWidgetItem(v.get("VersionId", "")))
            self._table.setItem(row, 1, QTableWidgetItem(str(v.get("LastModified", ""))))
            self._table.setItem(row, 2, QTableWidgetItem(str(v.get("Size", ""))))
            self._table.setItem(row, 3, QTableWidgetItem("✓" if v.get("IsLatest") else ""))
        layout.addWidget(self._table)
        btn_row = QHBoxLayout()
        restore = QPushButton("Restore This Version")
        restore.clicked.connect(self._on_restore)
        btn_row.addStretch()
        btn_row.addWidget(restore)
        layout.addLayout(btn_row)

    def _on_restore(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            ver_id = self._table.item(row, 0).text()
            self.restore_requested.emit(ver_id)
            self.accept()
