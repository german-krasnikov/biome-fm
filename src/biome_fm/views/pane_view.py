"""PaneView — passive dual-pane file manager widget."""

from __future__ import annotations

from pathlib import Path

from biome_fm.models.directory_model import COL_NAME, DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem
from biome_fm.qt import (
    QHeaderView,
    QLabel,
    QLineEdit,
    QModelIndex,
    Qt,
    QTableView,
    QVBoxLayout,
    QWidget,
    Signal,
)


class PaneView(QWidget):
    item_activated = Signal(object)          # FileItem
    path_change_requested = Signal(object)   # Path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = DirectoryModel(self)
        self._proxy = DirSortFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._path_bar = QLineEdit()
        self._path_bar.setPlaceholderText("Path...")
        self._path_bar.returnPressed.connect(self._on_path_entered)
        layout.addWidget(self._path_bar)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(
            COL_NAME, QHeaderView.ResizeMode.Stretch
        )
        self._table.activated.connect(self._on_activated)
        layout.addWidget(self._table)

        self._proxy.sort(COL_NAME, Qt.SortOrder.AscendingOrder)

        self._status_label = QLabel()
        layout.addWidget(self._status_label)

    # ── PaneViewProtocol implementation ──────────────────────────────────────

    def set_items(self, items: list[FileItem]) -> None:
        self._model.set_items(items)

    def set_path(self, path: Path) -> None:
        self._path_bar.setText(str(path))

    def show_error(self, message: str) -> None:
        self._path_bar.setText(f"Error: {message}")

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    # ── query ─────────────────────────────────────────────────────────────────

    def selected_items(self) -> list[FileItem]:
        rows = {idx.row() for idx in self._table.selectedIndexes()}
        result = []
        for proxy_row in rows:
            src = self._proxy.mapToSource(self._proxy.index(proxy_row, 0))
            item = self._model.item_at(src.row())
            if item is not None:
                result.append(item)
        return result

    def current_item(self) -> FileItem | None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            return None
        src = self._proxy.mapToSource(idx)
        return self._model.item_at(src.row())

    # ── internal ──────────────────────────────────────────────────────────────

    def _on_activated(self, proxy_index: QModelIndex) -> None:
        src = self._proxy.mapToSource(proxy_index)
        item = self._model.item_at(src.row())
        if item is not None:
            self.item_activated.emit(item)

    def _on_path_entered(self) -> None:
        text = self._path_bar.text().strip()
        if text:
            self.path_change_requested.emit(Path(text))
