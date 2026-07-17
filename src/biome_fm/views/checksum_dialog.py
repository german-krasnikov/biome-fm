"""Checksum dialog — compute and display file hashes."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

_ALGOS = ["xxhash", "blake3", "md5", "sha256"]


class ChecksumDialog(QDialog):
    def __init__(self, paths: list[Path], parent=None) -> None:
        super().__init__(parent)
        self._paths = paths
        self.setWindowTitle("Checksum")
        self.resize(600, 300)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Algorithm:"))
        self._combo = QComboBox()
        self._combo.addItems(_ALGOS)
        row.addWidget(self._combo)
        row.addStretch()
        btn_compute = QPushButton("Compute")
        btn_compute.clicked.connect(self._compute)
        row.addWidget(btn_compute)
        layout.addLayout(row)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["File", "Hash"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        bbox = QDialogButtonBox()
        btn_copy = QPushButton("Copy")
        btn_copy.clicked.connect(self._copy)
        bbox.addButton(btn_copy, QDialogButtonBox.ButtonRole.ActionRole)
        bbox.addButton(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _compute(self) -> None:
        from biome_fm.commands.checksum_cmd import ChecksumCmd

        algo = self._combo.currentText()
        results = ChecksumCmd(self._paths, algorithm=algo).execute()
        self._table.setRowCount(0)
        for path_str, digest in results.items():
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(Path(path_str).name))
            self._table.setItem(row, 1, QTableWidgetItem(digest))

    def _copy(self) -> None:
        lines = []
        for row in range(self._table.rowCount()):
            name = self._table.item(row, 0)
            digest = self._table.item(row, 1)
            if name and digest:
                lines.append(f"{digest.text()}  {name.text()}")
        if lines:
            QGuiApplication.clipboard().setText("\n".join(lines))
