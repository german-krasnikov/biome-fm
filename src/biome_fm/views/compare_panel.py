"""ComparePanel — Qt view for directory comparison results."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus

_COLUMNS = ("Name", "Status", "Left Size", "Right Size")

_STATUS_COLOR: dict[CompareStatus, QColor] = {
    CompareStatus.LEFT_ONLY:   QColor("#e06c75"),
    CompareStatus.RIGHT_ONLY:  QColor("#98c379"),
    CompareStatus.NEWER_LEFT:  QColor("#e5c07b"),
    CompareStatus.NEWER_RIGHT: QColor("#e5c07b"),
    CompareStatus.DIFF_SIZE:   QColor("#61afef"),
}


class CompareModel(QAbstractTableModel):
    def __init__(self, entries: list[CompareEntry], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries = entries

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 4

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._entries):
            return None
        e = self._entries[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return e.name
            if col == 1:
                return e.status.value
            if col == 2:
                return e.left.size if e.left else ""
            if col == 3:
                return e.right.size if e.right else ""
        if role == Qt.ItemDataRole.ForegroundRole and col == 1:
            return _STATUS_COLOR.get(e.status)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]
        return None


class ComparePanel(QWidget):
    sync_left_to_right_requested = Signal(list)
    sync_right_to_left_requested = Signal(list)
    diff_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar()
        self._act_sync_lr = toolbar.addAction("Sync L→R")
        self._act_sync_rl = toolbar.addAction("Sync R→L")
        self._act_diff    = toolbar.addAction("View Diff")

        self._table = QTableView()
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        self._status_label = QLabel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)

        self._act_sync_lr.triggered.connect(self._on_sync_lr)
        self._act_sync_rl.triggered.connect(self._on_sync_rl)
        self._act_diff.triggered.connect(self._on_diff)

    # ------------------------------------------------------------------
    def set_entries(self, entries: list[CompareEntry]) -> None:
        self._table.setModel(CompareModel(entries, self))
        diffs = sum(1 for e in entries if e.status != CompareStatus.EQUAL)
        self._status_label.setText(f"{diffs} difference(s) out of {len(entries)} entries")

    def _selected_entries(self) -> list[CompareEntry]:
        model: CompareModel | None = self._table.model()  # type: ignore[assignment]
        if model is None:
            return []
        rows = {idx.row() for idx in self._table.selectionModel().selectedRows()}
        return [model._entries[r] for r in sorted(rows)]

    def _on_sync_lr(self) -> None:
        self.sync_left_to_right_requested.emit(self._selected_entries())

    def _on_sync_rl(self) -> None:
        self.sync_right_to_left_requested.emit(self._selected_entries())

    def _on_diff(self) -> None:
        sel = self._selected_entries()
        if sel:
            self.diff_requested.emit(sel[0])
