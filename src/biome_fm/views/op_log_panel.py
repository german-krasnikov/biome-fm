"""OpLogPanel — live log of file operations."""
from __future__ import annotations

import time
from collections import deque
from typing import Any

from biome_fm.qt import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QTableView,
    QVBoxLayout,
    QWidget,
)

_HEADERS = ("Time", "Operation", "Status", "Details")
_MAX_DEFAULT = 500


class OpLogModel(QAbstractTableModel):
    def __init__(self, max_entries: int = _MAX_DEFAULT, parent=None) -> None:
        super().__init__(parent)
        self._max = max_entries
        self._rows: deque[tuple[str, str, str, str]] = deque()

    def add_entry(self, op: str, status: str, details: str) -> None:
        ts = time.strftime("%H:%M:%S")
        if len(self._rows) >= self._max:
            self.beginRemoveRows(QModelIndex(), 0, 0)
            self._rows.popleft()
            self.endRemoveRows()
        row = len(self._rows)
        self.beginInsertRows(QModelIndex(), row, row)
        self._rows.append((ts, op, status, details))
        self.endInsertRows()

    # ── QAbstractTableModel ───────────────────────────────────────────────────

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._rows[index.row()][index.column()]

    def headerData(self, section: int, orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _HEADERS[section]
        return None


class OpLogPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = OpLogModel()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._view = QTableView()
        self._view.setModel(self._model)
        self._view.setUniformRowHeights(True)
        self._view.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._view)

    @property
    def model(self) -> OpLogModel:
        return self._model

    def log(self, op: str, status: str, details: str = "") -> None:
        self._model.add_entry(op, status, details)
