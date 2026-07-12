"""Bookmark dropdown menu widget."""
from __future__ import annotations

from biome_fm.qt import QHBoxLayout, QMenu, Qt, QToolButton, QWidget, Signal


class BookmarkMenu(QWidget):
    bookmark_chosen = Signal(object)  # Path
    edit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = None
        self._btn = QToolButton(self)
        self._btn.setText("★")
        self._btn.setFixedWidth(28)
        self._btn.setToolTip("Bookmarks (Ctrl+D to add)")
        self._btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._menu = QMenu(self._btn)
        self._menu.aboutToShow.connect(self._rebuild)
        self._btn.setMenu(self._menu)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._btn)

    def set_store(self, store) -> None:
        self._store = store

    def _rebuild(self) -> None:
        self._menu.clear()
        if self._store:
            for p in self._store.all():
                act = self._menu.addAction(p.name or str(p))
                act.setToolTip(str(p))
                act.triggered.connect(lambda checked, path=p: self.bookmark_chosen.emit(path))
        self._menu.addSeparator()
        self._menu.addAction("Edit Bookmarks...", self.edit_requested.emit)
