"""Conflict resolution dialog for file copy/move operations."""
from __future__ import annotations

import datetime
from pathlib import Path

from biome_fm.models.conflict_resolver import ConflictAction
from biome_fm.qt import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


def _file_info(path: Path) -> str:
    try:
        st = path.stat()
        size = st.st_size
        mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"{path.name}   {size:,} bytes   {mtime}"
    except OSError:
        return path.name


class ConflictDialog(QDialog):
    """Ask user what to do when a destination file already exists."""

    def __init__(self, src: object, dst: object, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.action = ConflictAction.CANCEL
        self.setWindowTitle("File Conflict")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("A file with this name already exists at the destination.")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        layout.addWidget(QLabel(f"<b>Source:</b> {_file_info(src)}"))   # type: ignore[arg-type]
        layout.addWidget(QLabel(f"<b>Destination:</b> {_file_info(dst)}"))  # type: ignore[arg-type]

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        btn_row = QHBoxLayout()
        for label, action in [
            ("Overwrite",     ConflictAction.OVERWRITE),
            ("Overwrite All", ConflictAction.OVERWRITE_ALL),
            ("Skip",          ConflictAction.SKIP),
            ("Skip All",      ConflictAction.SKIP_ALL),
            ("Rename",        ConflictAction.RENAME),
            ("Cancel",        ConflictAction.CANCEL),
        ]:
            btn = QPushButton(label)
            _action = action  # capture

            def _clicked(checked=False, a=_action):
                self.action = a
                self.accept()

            btn.clicked.connect(_clicked)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    @staticmethod
    def ask(src: object, dst: object, parent: object = None) -> ConflictAction:
        dlg = ConflictDialog(src, dst, parent)
        dlg.exec()
        return dlg.action
