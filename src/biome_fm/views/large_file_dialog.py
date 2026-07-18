"""Large File Finder dialog (F331)."""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
)


def scan_large_files(
    root: Path, min_bytes: int = 0, limit: int = 100
) -> list[tuple[Path, int]]:
    """Return top *limit* files under *root* by size, filtered by *min_bytes*."""
    results: list[tuple[Path, int]] = []
    for dirpath, _, files in os.walk(root):
        for fname in files:
            p = Path(dirpath) / fname
            try:
                size = p.stat().st_size
                if size >= min_bytes:
                    results.append((p, size))
            except OSError:
                pass
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


class _ScanThread(QThread):
    done = Signal(list)  # list[tuple[Path, int]]

    def __init__(self, root: Path, min_bytes: int, parent=None) -> None:
        super().__init__(parent)
        self._root = root
        self._min_bytes = min_bytes

    def run(self) -> None:
        self.done.emit(scan_large_files(self._root, self._min_bytes))


class _FileModel(QAbstractTableModel):
    _HEADERS = ("Path", "Size")

    def __init__(self, rows: list[tuple[Path, int]], parent=None) -> None:
        super().__init__(parent)
        self._rows = rows

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else 2

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        path, size = self._rows[index.row()]
        if index.column() == 0:
            return str(path)
        return _fmt(size)

    def path_at(self, row: int) -> Path:
        return self._rows[row][0]


class LargeFileDialog(QDialog):
    navigate_requested = Signal(Path)  # emits file path on double-click

    def __init__(self, root: Path, parent=None) -> None:
        super().__init__(parent)
        self._root = root
        self.setWindowTitle(f"Large Files — {root.name}")
        self.resize(700, 400)

        self._status = QLabel("Set threshold and press Scan.")
        self._spin = QSpinBox()
        self._spin.setRange(0, 10_000)
        self._spin.setValue(10)
        self._spin.setSuffix(" MB")
        self._scan_btn = QPushButton("Scan")
        self._scan_btn.clicked.connect(self._on_scan)

        top = QHBoxLayout()
        top.addWidget(QLabel("Min size:"))
        top.addWidget(self._spin)
        top.addWidget(self._scan_btn)
        top.addStretch()

        self._table = QTableView()
        self._table.setUniformRowHeights(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._on_double_click)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._status)
        layout.addWidget(self._table)

        self._thread: _ScanThread | None = None

    def _on_scan(self) -> None:
        if self._thread and self._thread.isRunning():
            return
        min_bytes = self._spin.value() * 1024 * 1024
        self._status.setText("Scanning…")
        self._scan_btn.setEnabled(False)
        self._thread = _ScanThread(self._root, min_bytes, self)
        self._thread.done.connect(self._on_done)
        self._thread.start()

    def _on_done(self, rows: list) -> None:
        model = _FileModel(rows, self)
        self._table.setModel(model)
        self._status.setText(f"{len(rows)} files found.")
        self._scan_btn.setEnabled(True)

    def _on_double_click(self, index: QModelIndex) -> None:
        model = self._table.model()
        if isinstance(model, _FileModel):
            self.navigate_requested.emit(model.path_at(index.row()))


def _fmt(n: int) -> str:
    s = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024:
            return f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} TB"
