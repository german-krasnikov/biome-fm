"""Dialog for selecting archive name and format."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

_FORMATS = ["zip", "tar.gz", "tar.bz2"]


class ArchiveFormatDialog(QDialog):
    def __init__(self, default_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Archive")

        self._name_edit = QLineEdit(default_name)
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(_FORMATS)

        form = QFormLayout()
        form.addRow("Archive name:", self._name_edit)
        form.addRow("Format:", self._fmt_combo)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(bbox)

    @property
    def archive_name(self) -> str:
        return self._name_edit.text()

    @property
    def format(self) -> str:
        return self._fmt_combo.currentText()
