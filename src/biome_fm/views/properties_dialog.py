"""File properties dialog — General info + Permissions tabs."""
from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from biome_fm.models.file_item import FileItem

_PERM_BITS = [
    ("Owner read", 0o400), ("Owner write", 0o200), ("Owner execute", 0o100),
    ("Group read",  0o040), ("Group write",  0o020), ("Group execute",  0o010),
    ("Other read",  0o004), ("Other write",  0o002), ("Other execute",  0o001),
]


class PropertiesDialog(QDialog):
    def __init__(self, item: FileItem, parent=None) -> None:
        super().__init__(parent)
        self._item = item
        self.setWindowTitle(f"Properties — {item.name}")
        self.resize(400, 300)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        self._tabs.addTab(self._general_tab(), "General")
        if sys.platform != "win32":
            self._tabs.addTab(self._permissions_tab(), "Permissions")
            self._tabs.addTab(self._xattr_tab(), "Extended Attrs")
        layout.addWidget(self._tabs)

        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Close
        )
        bbox.accepted.connect(self._save_comment)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._name_label = QLabel(self._item.name)
        form.addRow("Name:", self._name_label)

        self._path_label = QLabel(str(self._item.path.parent))
        form.addRow("Location:", self._path_label)

        self._size_label = QLabel(f"{self._item.size} bytes ({self._item.size_str})")
        form.addRow("Size:", self._size_label)

        mtime = datetime.fromtimestamp(self._item.modified).strftime("%Y-%m-%d %H:%M:%S")
        form.addRow("Modified:", QLabel(mtime))

        from biome_fm.models.finder_tags import get_finder_comment
        self._comment_edit = QTextEdit()
        self._comment_edit.setPlainText(get_finder_comment(self._item.path))
        self._comment_edit.setFixedHeight(60)
        form.addRow("Comment:", self._comment_edit)
        return w

    def _save_comment(self) -> None:
        from biome_fm.models.finder_tags import set_finder_comment
        set_finder_comment(self._item.path, self._comment_edit.toPlainText().strip())
        self.accept()

    def _permissions_tab(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        try:
            mode = int(self._item.permissions, 8) if self._item.permissions else self._item.path.stat().st_mode
        except (ValueError, OSError):
            mode = 0

        for i, (label, bit) in enumerate(_PERM_BITS):
            cb = QCheckBox(label)
            cb.setChecked(bool(mode & bit))
            cb.setEnabled(False)
            grid.addWidget(cb, i // 3, i % 3)
        return w

    def _xattr_tab(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        self._xattr_table = QTableWidget(0, 2)
        self._xattr_table.setHorizontalHeaderLabels(["Key", "Value"])
        self._xattr_table.horizontalHeader().setStretchLastSection(True)
        self._xattr_table.itemChanged.connect(self._on_xattr_changed)
        vbox.addWidget(self._xattr_table)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_xattr)
        rem_btn = QPushButton("Remove")
        rem_btn.clicked.connect(self._remove_xattr)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rem_btn)
        btn_row.addStretch()
        vbox.addLayout(btn_row)
        self._load_xattrs()
        return w

    def _load_xattrs(self) -> None:
        import os
        self._xattr_table.blockSignals(True)
        self._xattr_table.setRowCount(0)
        try:
            for key in os.listxattr(self._item.path, follow_symlinks=False):
                val = os.getxattr(self._item.path, key, follow_symlinks=False).decode(errors="replace")
                row = self._xattr_table.rowCount()
                self._xattr_table.insertRow(row)
                self._xattr_table.setItem(row, 0, QTableWidgetItem(key))
                self._xattr_table.setItem(row, 1, QTableWidgetItem(val))
        except (OSError, AttributeError):
            pass
        self._xattr_table.blockSignals(False)

    def _on_xattr_changed(self, item: QTableWidgetItem) -> None:
        import os
        if item.column() != 1:
            return
        key = self._xattr_table.item(item.row(), 0).text()
        try:
            os.setxattr(self._item.path, key, item.text().encode(), follow_symlinks=False)
        except (OSError, AttributeError):
            pass

    def _add_xattr(self) -> None:
        row = self._xattr_table.rowCount()
        self._xattr_table.insertRow(row)
        self._xattr_table.setItem(row, 0, QTableWidgetItem("user.new"))
        self._xattr_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_xattr(self) -> None:
        import os
        row = self._xattr_table.currentRow()
        if row < 0:
            return
        key = self._xattr_table.item(row, 0)
        if key:
            try:
                os.removexattr(self._item.path, key.text(), follow_symlinks=False)
            except (OSError, AttributeError):
                pass
        self._xattr_table.removeRow(row)
