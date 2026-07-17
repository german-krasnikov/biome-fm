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
    QLabel,
    QTabWidget,
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
        layout.addWidget(self._tabs)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
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
        return w

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
