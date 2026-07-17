"""JumpDialog — frecency-based quick-jump to directory."""
from __future__ import annotations

from biome_fm.qt import (
    QDialog,
    QKeySequence,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QShortcut,
    Qt,
    QVBoxLayout,
    Signal,
)


class JumpDialog(QDialog):
    path_selected = Signal(object)  # Path

    def __init__(self, entries, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quick Jump (Ctrl+J)")
        self.resize(500, 300)
        layout = QVBoxLayout(self)
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter…")
        self._filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self._filter)
        self._list = QListWidget()
        self._list.itemActivated.connect(self._on_activated)
        layout.addWidget(self._list)
        self._entries = list(entries)
        self._populate(self._entries)
        QShortcut(QKeySequence("Return"), self).activated.connect(self._on_return)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.reject)

    def _populate(self, entries) -> None:
        self._list.clear()
        for entry in entries:
            item = QListWidgetItem(str(entry.path))
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _apply_filter(self, text: str) -> None:
        q = text.lower()
        filtered = [e for e in self._entries if q in str(e.path).lower()]
        self._populate(filtered)

    def _on_activated(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.path_selected.emit(path)
            self.accept()

    def _on_return(self) -> None:
        cur = self._list.currentItem()
        if cur:
            self._on_activated(cur)
