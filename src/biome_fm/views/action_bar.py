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

    _BUTTONS: typing.ClassVar[list[tuple[str, str, str]]] = [
        ("F3 View",     "view_requested",   "Preview file (F3)"),
        ("F4 Edit",     "edit_requested",   "Edit file (F4)"),
        ("F5 Copy",     "copy_requested",   "Copy to other pane (F5)"),
        ("F6 Move",     "move_requested",   "Move to other pane (F6)"),
        ("F7 Mkdir",    "mkdir_requested",  "Create folder (F7)"),
        ("F8 Delete",   "delete_requested", "Delete selected (F8)"),
        ("F9 Rename",   "rename_requested", "Rename file (F9)"),
        ("Alt+F4 Exit", "exit_requested",   "Quit Biome FM (Alt+F4)"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        for label, sig_name, tip in self._BUTTONS:
            btn = QPushButton(label)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setToolTip(tip)
            btn.clicked.connect(getattr(self, sig_name))
            layout.addWidget(btn)
