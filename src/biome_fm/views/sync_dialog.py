"""SyncDialog — show directory diff and let the user sync."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.qt import (
    QColor,
    QDialog,
    QHBoxLayout,
    QPushButton,
    Qt,
    QVBoxLayout,
    Signal,
)

_STATUS_LABEL = {
    CompareStatus.EQUAL: "Equal",
    CompareStatus.LEFT_ONLY: "Left only",
    CompareStatus.RIGHT_ONLY: "Right only",
    CompareStatus.NEWER_LEFT: "Newer left",
    CompareStatus.NEWER_RIGHT: "Newer right",
    CompareStatus.DIFF_SIZE: "Diff size",
}

_STATUS_COLOR = {
    CompareStatus.LEFT_ONLY: "#4caf50",
    CompareStatus.NEWER_LEFT: "#ff9800",
    CompareStatus.RIGHT_ONLY: "#2196f3",
    CompareStatus.NEWER_RIGHT: "#ff9800",
    CompareStatus.DIFF_SIZE: "#9c27b0",
    CompareStatus.EQUAL: "#757575",
}


def _fmt_size(item) -> str:
    return item.size_str if item is not None else ""


class SyncDialog(QDialog):
    sync_requested = Signal(list, str)  # (list[CompareEntry], direction)

    def __init__(
        self,
        entries: list[CompareEntry],
        left_root: Path,
        right_root: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._entries = entries
        self._left_root = left_root
        self._right_root = right_root
        self.setWindowTitle("Synchronize Directories")
        self.resize(700, 450)
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["✓", "Name", "Status", "Left Size", "Right Size"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._btn_ltr = QPushButton("Sync →")
        self._btn_ltr.setToolTip("Copy left → right")
        self._btn_ltr.clicked.connect(lambda: self._emit("left_to_right"))

        self._btn_rtl = QPushButton("← Sync")
        self._btn_rtl.setToolTip("Copy right → left")
        self._btn_rtl.clicked.connect(lambda: self._emit("right_to_left"))

        self._btn_newer = QPushButton("Sync Newer")
        self._btn_newer.setToolTip("Copy newer file to the other side")
        self._btn_newer.clicked.connect(lambda: self._emit("newer_wins"))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        for b in (self._btn_ltr, self._btn_rtl, self._btn_newer):
            btn_row.addWidget(b)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _populate(self) -> None:
        self._table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            # checkbox item
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            is_equal = entry.status == CompareStatus.EQUAL
            default = Qt.CheckState.Unchecked if is_equal else Qt.CheckState.Checked
            chk.setCheckState(default)
            self._table.setItem(row, 0, chk)

            self._table.setItem(row, 1, QTableWidgetItem(entry.name))

            status_item = QTableWidgetItem(_STATUS_LABEL[entry.status])
            color = _STATUS_COLOR.get(entry.status, "#757575")
            status_item.setForeground(QColor(color))
            self._table.setItem(row, 2, status_item)

            self._table.setItem(row, 3, QTableWidgetItem(_fmt_size(entry.left)))
            self._table.setItem(row, 4, QTableWidgetItem(_fmt_size(entry.right)))

        self._table.resizeColumnsToContents()

    def _checked_entries(self) -> list[CompareEntry]:
        result = []
        for row in range(self._table.rowCount()):
            chk = self._table.item(row, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                result.append(self._entries[row])
        return result

    def _emit(self, direction: str) -> None:
        self.sync_requested.emit(self._checked_entries(), direction)
