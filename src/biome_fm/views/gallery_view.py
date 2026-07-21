"""Thumbnail gallery view — QListView IconMode with async thumbnail loading."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import SimpleQueue

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QListView, QVBoxLayout, QWidget

from biome_fm.models.file_item import FileItem

_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"})


class ThumbnailLoader:
    """Background thumbnail loading: ThreadPoolExecutor + SimpleQueue drain via QTimer."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._queue: SimpleQueue[tuple[Path, bytes]] = SimpleQueue()
        self._cache: dict[Path, QPixmap] = {}
        self._pending: set[Path] = set()

    def request(self, path: Path, callback) -> QPixmap | None:
        """Return cached pixmap or None (delivered later via drain)."""
        if path in self._cache:
            return self._cache[path]
        if path in self._pending or path.suffix.lower() not in _IMAGE_EXTS:
            return None
        self._pending.add(path)
        self._executor.submit(self._load, path)
        return None

    def _load(self, path: Path) -> None:
        try:
            self._queue.put((path, path.read_bytes()))
        except Exception:
            self._pending.discard(path)

    def drain(self) -> list[tuple[Path, QPixmap]]:
        """Drain queue on main thread. Returns list of (path, pixmap) ready."""
        results = []
        while not self._queue.empty():
            path, data = self._queue.get_nowait()
            pm = QPixmap()
            pm.loadFromData(data)
            if not pm.isNull():
                pm = pm.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self._cache[path] = pm
                results.append((path, pm))
            self._pending.discard(path)
        # ponytail: simple dict eviction (insertion-order), upgrade to LRU if 500 proves too small
        while len(self._cache) > 500:
            del self._cache[next(iter(self._cache))]
        return results

    def cancel_all(self) -> None:
        self._pending.clear()
        while not self._queue.empty():
            self._queue.get_nowait()


class GalleryView(QWidget):
    """QListView in IconMode with async thumbnail loading."""

    file_activated = Signal(object)   # FileItem
    selection_changed = Signal(list)  # list[FileItem]

    THUMB_SIZE = 128

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self._list = QListView(self)
        self._list.setModel(self._model)
        self._list.setViewMode(QListView.ViewMode.IconMode)
        self._list.setIconSize(QSize(self.THUMB_SIZE, self.THUMB_SIZE))
        self._list.setResizeMode(QListView.ResizeMode.Adjust)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.setWrapping(True)
        self._list.setSpacing(8)
        self._list.activated.connect(self._on_activated)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)

        self._items: list[FileItem] = []
        self._path_to_row: dict[Path, int] = {}
        self._loader = ThumbnailLoader()
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._drain_thumbs)

    def set_items(self, items: list[FileItem], **kwargs) -> None:
        self._timer.stop()
        self._loader.cancel_all()
        self._model.clear()
        self._items = list(items)
        self._path_to_row.clear()
        for i, item in enumerate(items):
            si = QStandardItem(item.name)
            si.setEditable(False)
            cached = self._loader.request(item.path, None)
            if cached:
                si.setIcon(QIcon(cached))
            self._model.appendRow(si)
            self._path_to_row[item.path] = i
        if items:
            self._timer.start()

    def _drain_thumbs(self) -> None:
        results = self._loader.drain()
        for path, pixmap in results:
            row = self._path_to_row.get(path)
            if row is not None:
                item = self._model.item(row)
                if item:
                    item.setIcon(QIcon(pixmap))
        if not self._loader._pending:
            self._timer.stop()

    def _on_activated(self, index) -> None:
        row = index.row()
        if 0 <= row < len(self._items):
            self.file_activated.emit(self._items[row])

    def current_item(self) -> FileItem | None:
        idx = self._list.currentIndex()
        if idx.isValid() and 0 <= idx.row() < len(self._items):
            return self._items[idx.row()]
        return None
