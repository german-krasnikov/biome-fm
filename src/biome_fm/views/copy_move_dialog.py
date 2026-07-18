"""TC-style copy/move destination dialog with editable path + history (F223)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


def _heading(op: str, count: int) -> str:
    noun = "item" if count == 1 else "items"
    return f"{'Copy' if op == 'copy' else 'Move'} {count} {noun} to:"


class CopyMoveDialog(QDialog):
    def __init__(
        self,
        op: str,
        sources: list[Path],
        default_dest: Path,
        history: list[str],
        parent: object = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Copy" if op == "copy" else "Move")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel(_heading(op, len(sources))))

        row = QHBoxLayout()
        self._dest_combo = QComboBox()
        self._dest_combo.setEditable(True)
        self._dest_combo.addItem(str(default_dest))
        for h in history:
            if h != str(default_dest):
                self._dest_combo.addItem(h)
        self._dest_combo.setCurrentIndex(0)
        row.addWidget(self._dest_combo, 1)

        browse = QPushButton("…")
        browse.setFixedWidth(32)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        layout.addLayout(row)

        self._verify_cb = QCheckBox("Verify checksum after copy")
        if op == "copy":
            layout.addWidget(self._verify_cb)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,  # type: ignore[arg-type]
            "Select Destination",
            self._dest_combo.currentText(),
        )
        if path:
            self._dest_combo.setCurrentText(path)

    @property
    def destination(self) -> Path:
        return Path(self._dest_combo.currentText())

    @property
    def verify_enabled(self) -> bool:
        return self._verify_cb.isChecked()

    @staticmethod
    def ask(
        op: str,
        sources: list[Path],
        default_dest: Path,
        history: list[str],
        parent: object = None,
    ) -> Path | None:
        dlg = CopyMoveDialog(op, sources, default_dest, history, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.destination
        return None
