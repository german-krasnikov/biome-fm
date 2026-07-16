"""SearchResultsModel + SearchResultsPanel."""
from __future__ import annotations

import datetime

from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.qt import (
    QAbstractTableModel,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QModelIndex,
    QProgressBar,
    QPushButton,
    Qt,
    QTableView,
    QVBoxLayout,
    QWidget,
    Signal,
)


class SearchResultsModel(QAbstractTableModel):
    HEADERS = ("Name", "Location", "Size", "Modified")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[SearchResult] = []

    def append(self, result: SearchResult) -> None:
        r = len(self._rows)
        self.beginInsertRows(QModelIndex(), r, r)
        self._rows.append(result)
        self.endInsertRows()

    def append_batch(self, results: list[SearchResult]) -> None:
        if not results:
            return
        first = len(self._rows)
        last = first + len(results) - 1
        self.beginInsertRows(QModelIndex(), first, last)
        self._rows.extend(results)
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()

    def result_at(self, row: int) -> SearchResult | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                return r.item.name
            if col == 1:
                return str(r.item.path.parent)
            if col == 2:
                return r.item.size_str
            if col == 3:
                if r.item.modified == 0.0:
                    return ""
                return datetime.datetime.fromtimestamp(r.item.modified).strftime("%Y-%m-%d %H:%M")
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(r.item.path)
        if role == Qt.ItemDataRole.UserRole:
            return r
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section] if 0 <= section < len(self.HEADERS) else None
        return None


class SearchResultsPanel(QWidget):
    close_requested = Signal()
    detach_requested = Signal()
    navigate_to_file = Signal(object, str)  # (parent_dir: Path, filename: str)
    stop_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = SearchResultsModel()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2)
        self._title = QLabel("Search Results")
        header.addWidget(self._title)
        header.addStretch()
        btn_detach = QPushButton("⬒")
        btn_detach.setFixedSize(24, 24)
        btn_detach.setToolTip("Detach to window")
        btn_detach.clicked.connect(self.detach_requested)
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setToolTip("Close")
        btn_close.clicked.connect(self.close_requested)
        header.addWidget(btn_detach)
        header.addWidget(btn_close)
        layout.addLayout(header)

        # Status + Stop
        status_row = QHBoxLayout()
        self._status = QLabel("Ready")
        status_row.addWidget(self._status, 1)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setFixedWidth(60)
        self._stop_btn.clicked.connect(self.stop_requested)
        self._stop_btn.hide()
        status_row.addWidget(self._stop_btn)
        layout.addLayout(status_row)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.hide()
        layout.addWidget(self._progress)

        # Table
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        vh = self._table.verticalHeader()
        vh.setVisible(False)
        vh.setDefaultSectionSize(22)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(0, 150)
        self._table.setColumnWidth(2, 70)
        self._table.setColumnWidth(3, 130)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

    def on_search_started(self, query: str) -> None:
        self._model.clear()
        self._title.setText(f"Search: {query}")
        self._status.setText("Searching...")
        self._progress.show()
        self._stop_btn.show()

    def add_result(self, result: SearchResult) -> None:
        self._model.append(result)
        self._status.setText(f"Found {self._model.rowCount()}...")

    def add_results(self, results: list[SearchResult]) -> None:
        self._model.append_batch(results)
        self._status.setText(f"Found {self._model.rowCount()}...")

    @property
    def result_count(self) -> int:
        return self._model.rowCount()

    def on_finished(self, count: int) -> None:
        self._progress.hide()
        self._stop_btn.hide()
        self._status.setText(f"Found {count} items")

    def on_cancelled(self) -> None:
        self._progress.hide()
        self._stop_btn.hide()
        self._status.setText(f"Cancelled — {self._model.rowCount()} items found")

    def clear(self) -> None:
        self._model.clear()
        self._status.setText("Ready")

    def _show_context_menu(self, pos) -> None:
        idx = self._table.indexAt(pos)
        if not idx.isValid():
            return
        result = self._model.result_at(idx.row())
        if result is None:
            return
        menu = QMenu(self.window())
        menu.addAction("Go to File", lambda: self.navigate_to_file.emit(
            result.item.path.parent, result.item.name))
        menu.addAction("Copy Path", lambda: QApplication.clipboard().setText(str(result.item.path)))
        menu.popup(self._table.mapToGlobal(pos))

    def _on_double_click(self, index: QModelIndex) -> None:
        result = self._model.result_at(index.row())
        if result is not None:
            self.navigate_to_file.emit(result.item.path.parent, result.item.name)
