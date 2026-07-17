"""Shared panel chrome: detach + close buttons."""
from __future__ import annotations

from collections.abc import Callable

from biome_fm.qt import QHBoxLayout, QPushButton


def add_panel_buttons(header: QHBoxLayout, detach: Callable, close: Callable) -> None:
    """Append detach (⬒) and close (✕) buttons to header layout."""
    btn_detach = QPushButton("⬒")
    btn_detach.setFixedSize(24, 24)
    btn_detach.setToolTip("Detach to window")
    btn_detach.clicked.connect(detach)
    btn_close = QPushButton("✕")
    btn_close.setFixedSize(24, 24)
    btn_close.setToolTip("Close")
    btn_close.clicked.connect(close)
    header.addWidget(btn_detach)
    header.addWidget(btn_close)
