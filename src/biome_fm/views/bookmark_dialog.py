"""Bookmark edit dialog."""
from __future__ import annotations

from pathlib import Path

from biome_fm.qt import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    Qt,
    QVBoxLayout,
)


class BookmarkDialog(QDialog):
    _DND_MIME = "application/x-biome-fm-paths"

    def __init__(self, store, bus=None, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("Edit Bookmarks")
        self.setAcceptDrops(True)
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
        self._btn_add = QPushButton("Add")
        self._btn_remove = QPushButton("Remove")
        self._btn_up = QPushButton("Up")
        self._btn_down = QPushButton("Down")
        self._btn_edit = QPushButton("Edit Path")
        self._btn_rename = QPushButton("Rename")
        self._btn_close = QPushButton("Close")

        for btn in (self._btn_add, self._btn_remove, self._btn_up, self._btn_down,
                    self._btn_edit, self._btn_rename):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_close)
        layout.addLayout(btn_layout)

        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(self._on_up)
        self._btn_down.clicked.connect(self._on_down)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_rename.clicked.connect(self._on_rename)
        self._btn_close.clicked.connect(self.close)

    def _refresh(self) -> None:
        row = self._list.currentRow()
        self._list.clear()
        for p in self._store.all():
            label_text = self._store.display_label(p)
            label = f"{label_text}  —  {p}" if label_text != str(p) else str(p)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(p))
            self._list.addItem(item)
        if row >= 0:
            self._list.setCurrentRow(min(row, self._list.count() - 1))

    def _selected_path(self) -> Path | None:
        item = self._list.currentItem()
        if not item:
            return None
        return Path(item.data(Qt.ItemDataRole.UserRole))

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
            self._store.replace(p, Path(text.strip()).expanduser())
            self._publish()
            self._refresh()

    def _on_rename(self) -> None:
        p = self._selected_path()
        if not p:
            return
        current = self._store.get_name(p)
        name, ok = QInputDialog.getText(self, "Rename Bookmark", "Display name:", text=current)
        if ok:
            self._store.set_name(p, name.strip())
            self._publish()
            self._refresh()

    def _publish(self) -> None:
        if self._bus:
            from biome_fm.event_bus import BookmarkChanged
            self._bus.publish(BookmarkChanged())

    def _on_add(self) -> None:
        text, ok = QInputDialog.getText(self, "Add Bookmark", "Path:")
        if ok and text.strip():
            self._store.add(Path(text.strip()).expanduser())
            self._publish()
            self._refresh()

    def _handle_drop(self, mime) -> None:
        if mime.hasFormat(self._DND_MIME):
            raw = mime.data(self._DND_MIME).data().decode()
            paths = [Path(p) for p in raw.splitlines() if p.strip()]
        elif mime.hasUrls():
            paths = [Path(u.toLocalFile()) for u in mime.urls() if u.isLocalFile()]
        else:
            return
        if not paths:
            return
        before = len(self._store.all())
        for p in paths:
            self._store.add(p)
        if len(self._store.all()) > before:
            self._publish()
        self._refresh()

    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md.hasFormat(self._DND_MIME) or any(u.isLocalFile() for u in md.urls()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        self._handle_drop(event.mimeData())
        event.acceptProposedAction()
