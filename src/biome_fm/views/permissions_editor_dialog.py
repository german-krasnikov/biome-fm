"""Bulk permissions editor dialog (POSIX only) (F210)."""
from __future__ import annotations

import os
import stat
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

_BITS = [
    ("Owner read",   0o400), ("Owner write",  0o200), ("Owner exec",  0o100),
    ("Group read",   0o040), ("Group write",  0o020), ("Group exec",  0o010),
    ("Others read",  0o004), ("Others write", 0o002), ("Others exec", 0o001),
]


def _mode_from_checkboxes(checks: list[QCheckBox]) -> int:
    return sum(bit for (_, bit), cb in zip(_BITS, checks) if cb.isChecked())


def _initial_mode(paths: list[Path]) -> int:
    """Read mode from first path's current permissions; fall back to 0o644."""
    try:
        return stat.S_IMODE(paths[0].stat().st_mode)
    except (OSError, IndexError):
        return 0o644


class PermissionsEditorDialog(QDialog):
    def __init__(self, paths: list[Path], parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle(f"Permissions — {len(paths)} item(s)")
        layout = QVBoxLayout(self)

        box = QGroupBox("New permissions")
        grid = QFormLayout(box)
        self._checks: list[QCheckBox] = []
        initial = _initial_mode(paths)
        for label, bit in _BITS:
            cb = QCheckBox()
            cb.setChecked(bool(initial & bit))
            grid.addRow(label, cb)
            self._checks.append(cb)
        layout.addWidget(box)

        row = QHBoxLayout()
        row.addWidget(QLabel("Recursive"))
        self._recursive = QCheckBox()
        row.addWidget(self._recursive)
        row.addStretch()
        layout.addLayout(row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def mode(self) -> int:
        return _mode_from_checkboxes(self._checks)

    @property
    def recursive(self) -> bool:
        return self._recursive.isChecked()

    @staticmethod
    def ask(paths: list[Path], parent: object = None) -> tuple[int, bool] | None:
        if os.name != "posix":
            return None
        dlg = PermissionsEditorDialog(paths, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.mode, dlg.recursive
        return None
