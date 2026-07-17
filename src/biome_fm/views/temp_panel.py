"""TempPanel — dialog for browsing and cleaning temp files."""
from __future__ import annotations

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from biome_fm.presenters.temp_presenter import TempEntry, delete_entries, list_temp_entries
from biome_fm.qt import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    Signal,
)


class TempPanel(QDialog):
    deleted = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Temp Files")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Name", "Size", "Age (days)"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._btn_old = QPushButton("Delete >7 days")
        self._btn_old.clicked.connect(self._delete_old)
        self._btn_all = QPushButton("Delete All")
        self._btn_all.clicked.connect(self._delete_all)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._refresh)
        btn_row.addWidget(self._btn_old)
        btn_row.addWidget(self._btn_all)
        btn_row.addStretch()
        btn_row.addWidget(btn_refresh)
        layout.addLayout(btn_row)

        self._entries: list[TempEntry] = []
        self._refresh()

    def _refresh(self) -> None:
        self._entries = list_temp_entries()
        self._table.setRowCount(0)
        for i, e in enumerate(self._entries):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(e.path.name))
            self._table.setItem(i, 1, QTableWidgetItem(f"{e.size:,}"))
            self._table.setItem(i, 2, QTableWidgetItem(f"{e.age_days:.1f}"))

    def _delete_old(self) -> None:
        old = [e for e in self._entries if e.age_days > 7]
        n = delete_entries(old)
        self._refresh()
        self.deleted.emit(n)

    def _delete_all(self) -> None:
        if (
            QMessageBox.question(self, "Confirm", "Delete all temp files?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        n = delete_entries(self._entries)
        self._refresh()
        self.deleted.emit(n)
