"""UploadQueuePanel — shows pending/active/done upload progress (F304)."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class UploadQueuePanel(QWidget):
    """Passive view: shows upload queue items with status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: dict[int, QListWidgetItem] = {}
        self._list = QListWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Upload Queue"))
        layout.addWidget(self._list)

    def add_upload(self, task_id: int, name: str, total_bytes: int = 0) -> None:
        item = QListWidgetItem(f"⏳ {name}")
        self._items[task_id] = item
        self._list.addItem(item)

    def on_progress(self, task_id: int, bytes_done: int, bytes_total: int) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        pct = int(bytes_done * 100 / bytes_total) if bytes_total else 0
        name = item.text().split(" ", 1)[-1]
        item.setText(f"⬆ {name} ({pct}%)")

    def on_done(self, task_id: int) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        name = item.text().split(" ", 1)[-1]
        item.setText(f"✓ {name}")

    def on_error(self, task_id: int, error: str) -> None:
        item = self._items.get(task_id)
        if item is None:
            return
        name = item.text().split(" ", 1)[-1]
        item.setText(f"✗ {name}: {error}")
