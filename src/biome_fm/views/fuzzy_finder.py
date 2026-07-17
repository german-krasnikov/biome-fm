"""Fuzzy file finder overlay widget."""
from __future__ import annotations

import queue
import threading
from pathlib import Path

from biome_fm.presenters.fuzzy_presenter import FuzzyPresenter
from biome_fm.qt import (
    QFrame,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
    Signal,
)


class FuzzyFinder(QFrame):
    file_chosen = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(500)
        self.setMaximumHeight(400)

        self._presenter = FuzzyPresenter()
        self._paths: list[Path] = []
        self._root = Path.home()
        self._cancel = threading.Event()
        self._queue: queue.SimpleQueue = queue.SimpleQueue()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search files...")
        layout.addWidget(self._input)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._do_filter)
        self._input.textChanged.connect(lambda _: self._debounce.start())

        self._drain_timer = QTimer()
        self._drain_timer.setInterval(100)
        self._drain_timer.timeout.connect(self._drain)

        self._input.returnPressed.connect(self._accept)
        self._list.itemActivated.connect(self._on_item_activated)
        self._input.installEventFilter(self)

    def open(self, root: Path) -> None:
        self._root = root
        self._paths = []
        self._cancel.set()
        self._cancel = threading.Event()
        self._input.clear()
        self._list.clear()
        self.show()
        self._input.setFocus()
        if self.parent():
            pw = self.parent().width()  # type: ignore[union-attr]
            self.move((pw - self.width()) // 2, 40)
        self._presenter.scan(root, self._cancel, self._queue.put)
        self._drain_timer.start()

    def _drain(self) -> None:
        try:
            paths = self._queue.get_nowait()
            self._paths = paths
            self._do_filter()
            self._drain_timer.stop()
        except queue.Empty:
            pass

    def _do_filter(self) -> None:
        query = self._input.text().strip()
        matches = self._presenter.score(query, self._paths, self._root)
        self._list.clear()
        for m in matches:
            item = QListWidgetItem(m.label)
            item.setData(Qt.ItemDataRole.UserRole, m.path)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _accept(self) -> None:
        item = self._list.currentItem()
        if item:
            self.file_chosen.emit(item.data(Qt.ItemDataRole.UserRole))
        self.hide()
        self._cancel.set()

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.file_chosen.emit(path)
        self.hide()
        self._cancel.set()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self._cancel.set()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        if obj is self._input and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                row = self._list.currentRow()
                if row < self._list.count() - 1:
                    self._list.setCurrentRow(row + 1)
                return True
            if key == Qt.Key.Key_Up:
                row = self._list.currentRow()
                if row > 0:
                    self._list.setCurrentRow(row - 1)
                return True
        return super().eventFilter(obj, event)
