"""DirectoryModel -- thin QAbstractTableModel adapter over list[FileItem]."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from biome_fm.models.file_item import FileItem
from biome_fm.models.highlight_rules import HighlightRule, match_highlight
from biome_fm.qt import (
    QAbstractTableModel,
    QBrush,
    QColor,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    QWidget,
)

COL_NAME, COL_SIZE, COL_MODIFIED, COL_EXT = range(4)
HEADERS = ("Name", "Size", "Modified", "Ext")

_CODE = (".py", ".js", ".ts", ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb")
_DOCS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".md", ".txt", ".rtf")

_EXT_COLORS: dict[str, str] = {
    **{e: "#D55E00" for e in (".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar")},
    **{e: "#CC79A7" for e in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico")},
    **{e: "#009E73" for e in _CODE},
    **{e: "#0072B2" for e in _DOCS},
    **{e: "#E69F00" for e in (".mp3", ".mp4", ".wav", ".flac", ".avi", ".mkv", ".mov")},
    **{e: "#009E73" for e in (".exe", ".sh", ".bat", ".cmd", ".app")},
}
_DIM = "#565F89"
_GIT_COLORS: dict[str, str] = {
    "M ": "#E69F00", " M": "#E69F00", "MM": "#E69F00",
    "A ": "#009E73", "AM": "#009E73",
    "D ": "#E74C3C", " D": "#E74C3C",
    "??": "#808080",
    "R ": "#CC79A7", " R": "#CC79A7",
}
_GIT_DIR_DIRTY = "#E69F00"

_Idx = QModelIndex | QPersistentModelIndex


def _fmt_size(size: int) -> str:
    s = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024:
            return f"{s:.0f} {unit}" if unit == "B" else f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} PB"


class DirectoryModel(QAbstractTableModel):
    _BATCH = 200

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_items: list[FileItem] = []
        self._items: list[FileItem] = []
        self._fetch_offset: int = 0
        self._marks: set[Path] = set()
        self._cut_paths: set[Path] = set()
        self._git_statuses: dict[Path, str] = {}
        self._git_dirty_dirs: frozenset[Path] = frozenset()
        self._highlight_rules: list[HighlightRule] = []
        self._tag_store: object | None = None  # TagStore, duck-typed
        self._dir_sizes: dict[Path, int] = {}

    def set_tag_store(self, store: object | None) -> None:
        self._tag_store = store

    def set_cut_paths(self, paths: set[Path]) -> None:
        self._cut_paths = set(paths)
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, self.columnCount() - 1),
                [Qt.ItemDataRole.ForegroundRole],
            )

    def set_items(self, items: list[FileItem]) -> None:
        self.beginResetModel()
        self._all_items = list(items)
        self._items = self._all_items[: self._BATCH]
        self._fetch_offset = len(self._items)
        self.endResetModel()

    def canFetchMore(self, parent: _Idx = QModelIndex()) -> bool:  # noqa: B008
        return self._fetch_offset < len(self._all_items)

    def fetchMore(self, parent: _Idx = QModelIndex()) -> None:  # noqa: B008
        remaining = len(self._all_items) - self._fetch_offset
        batch = min(remaining, self._BATCH)
        self.beginInsertRows(parent, self._fetch_offset, self._fetch_offset + batch - 1)
        self._items.extend(self._all_items[self._fetch_offset : self._fetch_offset + batch])
        self._fetch_offset += batch
        self.endInsertRows()

    def set_dir_size(self, path: Path, size: int) -> None:
        self._dir_sizes[path] = size
        for row, item in enumerate(self._items):
            if item.path == path:
                idx = self.index(row, COL_SIZE)
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.DisplayRole])

    def item_at(self, row: int) -> FileItem | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def flags(self, index: _Idx) -> Qt.ItemFlag:
        base = super().flags(index)
        if not index.isValid():
            return base
        item = self._items[index.row()]
        if item.name != "..":
            base |= Qt.ItemFlag.ItemIsDragEnabled
            if index.column() == COL_NAME:
                base |= Qt.ItemFlag.ItemIsEditable
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def set_marks(self, paths: set[Path]) -> None:
        self._marks = set(paths)
        if self._items:
            top = self.index(0, 0)
            bot = self.index(len(self._items) - 1, self.columnCount() - 1)
            self.dataChanged.emit(top, bot, [Qt.ItemDataRole.BackgroundRole])

    @property
    def marks(self) -> frozenset[Path]:
        return frozenset(self._marks)

    def set_git_status(self, statuses: dict[Path, str], dirty_dirs: frozenset[Path]) -> None:
        self._git_statuses = statuses
        self._git_dirty_dirs = dirty_dirs
        if self.rowCount():
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(self.rowCount() - 1, 0),
                [Qt.ItemDataRole.ForegroundRole],
            )

    def set_highlight_rules(self, rules: list[HighlightRule]) -> None:
        self._highlight_rules = rules
        if self.rowCount():
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(self.rowCount() - 1, 0),
                [Qt.ItemDataRole.ForegroundRole],
            )

    def rowCount(self, parent: _Idx = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent: _Idx = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(
        self, section: int, orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section] if 0 <= section < len(HEADERS) else None
        return None

    def data(self, index: _Idx, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.BackgroundRole:
            if item.path in self._marks:
                return QBrush(QColor(38, 111, 255, 80))
            return None
        if role == Qt.ItemDataRole.UserRole:
            return item
        if role == Qt.ItemDataRole.ForegroundRole:
            if item.path in self._cut_paths:
                return QBrush(QColor(128, 128, 128, 100))
            if item.path in self._git_statuses:
                color = _GIT_COLORS.get(self._git_statuses[item.path])
                if color:
                    return QBrush(QColor(color))
            if item.is_dir and item.path in self._git_dirty_dirs:
                return QBrush(QColor(_GIT_DIR_DIRTY))
            c = match_highlight(item.name, self._highlight_rules)
            if c:
                return QBrush(QColor(c))
            if self._tag_store is not None:
                tags = self._tag_store.get_tags(item.path)  # type: ignore[attr-defined]
                if tags:
                    tc = self._tag_store.tag_color(tags[0])  # type: ignore[attr-defined]
                    if tc:
                        return QBrush(QColor(tc))
            if item.name == ".." or item.is_dir:
                return None
            if item.name.startswith("."):
                return QBrush(QColor(_DIM))
            ext = Path(item.name).suffix.lower()
            color = _EXT_COLORS.get(ext)
            return QBrush(QColor(color)) if color else None
        if role == Qt.ItemDataRole.ToolTipRole:
            if item.name == "..":
                return ""
            parts = [str(item.path)]
            if not item.is_dir and item.modified:
                dt = datetime.datetime.fromtimestamp(item.modified)
                parts.append(f"Modified: {dt.strftime('%Y-%m-%d %H:%M')}")
            if not item.is_dir:
                parts.append(f"Size: {item.size_str}")
            return "\n".join(parts)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        col = index.column()
        if col == COL_NAME:
            return item.name
        if col == COL_SIZE:
            if item.is_dir and item.path in self._dir_sizes:
                return _fmt_size(self._dir_sizes[item.path])
            return item.size_str
        if col == COL_MODIFIED:
            if item.modified == 0.0:
                return ""
            return datetime.datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M")
        if col == COL_EXT:
            return Path(item.name).suffix.lstrip(".") if not item.is_dir else ""
        return None


def _scan_worker(
    vfs: object,
    path: "Path",
    cancel: "threading.Event",
    out_queue: "queue.SimpleQueue",
    batch_size: int = 50,
) -> None:
    """List *path* via *vfs* callable, emit batches into *out_queue*, sentinel None at end."""
    if cancel.is_set():
        return
    try:
        items = list(vfs(path))  # type: ignore[call-arg]
    except Exception as exc:
        if not cancel.is_set():
            out_queue.put(str(exc))
        return
    batch: list = []
    for item in items:
        if cancel.is_set():
            return
        batch.append(item)
        if len(batch) >= batch_size:
            out_queue.put(batch)
            batch = []
    if batch:
        out_queue.put(batch)
    out_queue.put(None)


def _fuzzy_match(pattern: str, text: str) -> bool:
    """True if every char in pattern appears in text in order (subsequence)."""
    it = iter(text.lower())
    return all(c in it for c in pattern.lower())


class DirSortFilterProxy(QSortFilterProxyModel):
    """Keeps '..' pinned first, dirs before files, then default sort."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._filter = ""
        self._show_hidden = False
        self._tag_filter: str | None = None
        self._tag_store: object | None = None

    def set_tag_filter(self, tag: str | None, store: object | None = None) -> None:
        self._tag_filter = tag
        self._tag_store = store
        self.invalidateRowsFilter()

    def set_filter(self, text: str) -> None:
        self._filter = text.lower()
        self.invalidateRowsFilter()

    def set_show_hidden(self, show: bool) -> None:
        self._show_hidden = show
        self.invalidateRowsFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: _Idx) -> bool:
        _role = Qt.ItemDataRole.UserRole
        model = self.sourceModel()
        item: FileItem | None = model.data(model.index(source_row, COL_NAME), _role)
        if item is None or item.name == "..":
            return True
        if not self._show_hidden and item.name.startswith("."):
            return False
        if self._tag_filter and self._tag_store is not None:
            tags = self._tag_store.get_tags(item.path)  # type: ignore[attr-defined]
            if self._tag_filter not in tags:
                return False
        if self._filter:
            return _fuzzy_match(self._filter, item.name)
        return True

    def lessThan(self, left: _Idx, right: _Idx) -> bool:
        _role = Qt.ItemDataRole.UserRole
        model = self.sourceModel()
        l_item: FileItem | None = model.data(left.sibling(left.row(), COL_NAME), _role)
        r_item: FileItem | None = model.data(right.sibling(right.row(), COL_NAME), _role)
        if l_item is None or r_item is None:
            return super().lessThan(left, right)
        # ".." pinned first regardless of sort order
        asc = self.sortOrder() == Qt.SortOrder.AscendingOrder
        if l_item.name == "..":
            return asc
        if r_item.name == "..":
            return not asc
        if l_item.is_dir != r_item.is_dir:
            return l_item.is_dir if asc else r_item.is_dir
        return super().lessThan(left, right)
