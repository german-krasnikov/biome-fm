"""Confirmation dialog for Copy / Move / Delete operations."""
from __future__ import annotations

from pathlib import Path

from biome_fm.qt import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    Qt,
    QVBoxLayout,
)

_MAX_SHOWN = 5
_TITLES = {"copy": "Copy", "move": "Move", "delete": "Delete"}


# ── pure helpers (unit-testable, no Qt) ──────────────────────────────────────

def _heading(op: str, count: int) -> str:
    label = _TITLES.get(op, op.capitalize())
    noun = "item" if count == 1 else "items"
    if op == "delete":
        return f"{label} {count} {noun}?"
    return f"{label} {count} {noun} to:"


def _format_paths(sources: list[Path], max_shown: int = _MAX_SHOWN) -> list[str]:
    shown = [str(p) for p in sources[:max_shown]]
    overflow = len(sources) - max_shown
    if overflow > 0:
        shown.append(f"… and {overflow} more")
    return shown


# ── dialog ───────────────────────────────────────────────────────────────────

class ConfirmDialog(QDialog):
    def __init__(
        self,
        op: str,
        sources: list[Path],
        dest: Path | None = None,
        parent: object = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        label = _TITLES.get(op, op.capitalize())
        self.setWindowTitle(f"{label} — Confirm")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # heading
        heading = QLabel(_heading(op, len(sources)))
        heading.setObjectName("confirm_heading")
        layout.addWidget(heading)

        # dest
        if dest is not None:
            dest_lbl = QLabel(str(dest))
            dest_lbl.setObjectName("confirm_dest")
            dest_lbl.setTextFormat(Qt.TextFormat.PlainText)
            dest_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(dest_lbl)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # paths
        for line in _format_paths(sources):
            lbl = QLabel(line)
            lbl.setObjectName("confirm_path")
            lbl.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(lbl)

        # warning for delete
        if op == "delete":
            warn = QLabel("This cannot be undone.")
            warn.setObjectName("confirm_warn")
            layout.addWidget(warn)

        # buttons
        btns = QDialogButtonBox()
        btns.addButton(QDialogButtonBox.StandardButton.Cancel)
        confirm_btn = btns.addButton(label, QDialogButtonBox.ButtonRole.AcceptRole)
        if op == "delete":
            confirm_btn.setObjectName("danger")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @staticmethod
    def confirm(
        op: str,
        sources: list[Path],
        dest: Path | None = None,
        parent: object = None,
    ) -> bool:
        return ConfirmDialog(op, sources, dest, parent).exec() == QDialog.DialogCode.Accepted
