"""InfoPanel — persistent sidebar showing file metadata."""
from __future__ import annotations

import mimetypes

from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from biome_fm.models.file_item import FileItem


class InfoPanel(QWidget):
    """Displays metadata for the cursor file."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        for key, label in [
            ("name", "Name"), ("size", "Size"), ("mtime", "Modified"),
            ("permissions", "Permissions"), ("mime", "Type"),
        ]:
            lbl = QLabel("—")
            lbl.setWordWrap(True)
            self._labels[key] = lbl
            form.addRow(label + ":", lbl)
        layout.addLayout(form)
        layout.addStretch()

    # ── InfoViewProtocol ─────────────────────────────────────────────────────

    def clear(self) -> None:
        for lbl in self._labels.values():
            lbl.setText("—")

    def update_fields(self, fields: dict) -> None:
        for key, lbl in self._labels.items():
            if key in fields:
                lbl.setText(fields[key])

    # ── Convenience ──────────────────────────────────────────────────────────

    def update_item(self, item: FileItem | None) -> None:
        if item is None:
            self.clear()
            return
        import datetime
        mtime_str = datetime.datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M:%S")
        mime, _ = mimetypes.guess_type(item.name)
        self.update_fields({
            "name": item.name,
            "size": item.size_str,
            "mtime": mtime_str,
            "permissions": item.permissions or "—",
            "mime": mime or "—",
        })
