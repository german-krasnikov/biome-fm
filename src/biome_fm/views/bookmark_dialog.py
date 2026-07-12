"""Bookmark edit dialog."""
from __future__ import annotations

from pathlib import Path

from biome_fm.qt import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class BookmarkDialog(QDialog):
    def __init__(self, store, bus=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Bookmarks")
        self.resize(400, 300)
        self._store = store
        self._bus = bus
        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        self._list = QListWidget()
        layout.addWidget(self._list, 1)

        btn_layout = QVBoxLayout()
        self._btn_remove = QPushButton("Remove")
        self._btn_up = QPushButton("Up")
        self._btn_down = QPushButton("Down")
        self._btn_edit = QPushButton("Edit Path")
        self._btn_close = QPushButton("Close")

        for btn in (self._btn_remove, self._btn_up, self._btn_down, self._btn_edit):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_close)
        layout.addLayout(btn_layout)

        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(self._on_up)
        self._btn_down.clicked.connect(self._on_down)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_close.clicked.connect(self.accept)

    def _refresh(self) -> None:
        row = self._list.currentRow()
        self._list.clear()
        for p in self._store.all():
            self._list.addItem(str(p))
        if row >= 0:
            self._list.setCurrentRow(min(row, self._list.count() - 1))

    def _selected_path(self) -> Path | None:
        item = self._list.currentItem()
        return Path(item.text()) if item else None

    def _on_remove(self) -> None:
        p = self._selected_path()
        if p:
            self._store.remove(p)
            self._publish()
            self._refresh()

    def _on_up(self) -> None:
        p = self._selected_path()
        if p:
            self._store.move_up(p)
            self._publish()
            self._refresh()

    def _on_down(self) -> None:
        p = self._selected_path()
        if p:
            self._store.move_down(p)
            self._publish()
            self._refresh()

    def _on_edit(self) -> None:
        p = self._selected_path()
        if not p:
            return
        text, ok = QInputDialog.getText(self, "Edit Path", "Path:", text=str(p))
        if ok and text.strip():
            self._store.replace(p, Path(text.strip()))
            self._publish()
            self._refresh()

    def _publish(self) -> None:
        if self._bus:
            from biome_fm.event_bus import BookmarkChanged  # noqa: PLC0415
            self._bus.publish(BookmarkChanged())
