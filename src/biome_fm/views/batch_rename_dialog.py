"""Batch rename dialog with live preview table."""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
)

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.rename_presenter import RenamePresenter, RenamePreview
from biome_fm.qt import (
    QCheckBox,
    QColor,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class BatchRenameDialog(QDialog):
    """Multi-rename dialog: find/replace (plain or regex) with live preview."""

    def __init__(self, items: list[FileItem], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Batch Rename")
        self._items = items
        self._presenter = RenamePresenter(items)
        self._previews: list[RenamePreview] = []

        # Inputs
        self._find = QLineEdit()
        self._find.setPlaceholderText("Find…")
        self._replace = QLineEdit()
        self._replace.setPlaceholderText("Replace with…")
        self._regex = QCheckBox("Regex")

        # Preview table
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Old Name", "New Name"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        # Buttons
        self._bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok = self._bbox.button(QDialogButtonBox.StandardButton.Ok)
        self._ok.setEnabled(False)
        self._bbox.accepted.connect(self.accept)
        self._bbox.rejected.connect(self.reject)

        # Layout
        row = QHBoxLayout()
        row.addWidget(QLabel("Find:"))
        row.addWidget(self._find)
        row.addWidget(QLabel("Replace:"))
        row.addWidget(self._replace)
        row.addWidget(self._regex)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self._table)
        layout.addWidget(self._bbox)

        self.resize(600, 400)
        self._find.textChanged.connect(self._update_preview)
        self._replace.textChanged.connect(self._update_preview)
        self._regex.toggled.connect(self._update_preview)

    def _update_preview(self) -> None:
        find = self._find.text()
        replace = self._replace.text()
        if not find:
            self._previews = []
            self._table.setRowCount(0)
            self._ok.setEnabled(False)
            return
        pattern = find if self._regex.isChecked() else re.escape(find)
        self._previews = self._presenter.apply_regex(pattern, replace)
        red = QColor("#ff6b6b")
        self._table.setRowCount(len(self._previews))
        has_valid = False
        for r, pv in enumerate(self._previews):
            self._table.setItem(r, 0, QTableWidgetItem(pv.original))
            cell = QTableWidgetItem(pv.new_name)
            if pv.conflict:
                cell.setBackground(red)
            self._table.setItem(r, 1, cell)
            if not pv.conflict and pv.new_name != pv.original:
                has_valid = True
        self._ok.setEnabled(has_valid)

    @property
    def renames(self) -> list[tuple[Path, str]]:
        """(old_path, new_name) pairs — conflicts and unchanged excluded."""
        return [
            (it.path, pv.new_name)
            for it, pv in zip(self._items, self._previews)
            if not pv.conflict and pv.new_name != it.name
        ]
