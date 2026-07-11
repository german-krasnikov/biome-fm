"""ActionBar — TC-style function key button strip."""
from __future__ import annotations

import typing

from biome_fm.qt import QHBoxLayout, QPushButton, Qt, QWidget, Signal


class ActionBar(QWidget):
    view_requested = Signal()
    edit_requested = Signal()
    copy_requested = Signal()
    move_requested = Signal()
    mkdir_requested = Signal()
    delete_requested = Signal()
    rename_requested = Signal()
    exit_requested = Signal()

    _BUTTONS: typing.ClassVar[list[tuple[str, str]]] = [
        ("F3 View", "view_requested"),
        ("F4 Edit", "edit_requested"),
        ("F5 Copy", "copy_requested"),
        ("F6 Move", "move_requested"),
        ("F7 Mkdir", "mkdir_requested"),
        ("F8 Delete", "delete_requested"),
        ("F9 Rename", "rename_requested"),
        ("Alt+F4 Exit", "exit_requested"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        for label, sig_name in self._BUTTONS:
            btn = QPushButton(label)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(getattr(self, sig_name))
            layout.addWidget(btn)
