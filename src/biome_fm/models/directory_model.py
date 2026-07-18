"""DirectoryModel -- thin QAbstractTableModel adapter over list[FileItem]."""

from __future__ import annotations

import datetime
from enum import Enum
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

COL_NAME, COL_SIZE, COL_MODIFIED, COL_EXT, COL_ATIME, COL_OWNER = range(6)
HEADERS = ("Name", "Size", "Modified", "Ext", "Accessed", "Owner")

# F278 — File Grouping
GROUP_ROLE = Qt.ItemDataRole.UserRole + 2


class GroupByMode(Enum):
    NONE = "none"
    KIND = "kind"
    DATE = "date"
    SIZE = "size"
    FIRST_LETTER = "first_letter"

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

_ARCHIVE_EXTS = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"}
_MEDIA_EXTS = {".mp3", ".mp4", ".wav", ".flac", ".avi", ".mkv", ".mov"}


def _group_key(item: FileItem, mode: GroupByMode) -> str:
    """Return group label for *item* given *mode*."""
    if mode == GroupByMode.NONE:
        return ""
    if mode == GroupByMode.FIRST_LETTER:
        return item.name[0].upper() if item.name else ""
    if mode == GroupByMode.KIND:
        if item.is_dir:
            return "Folders"
        ext = Path(item.name).suffix.lower()
        if ext in set(_CODE):
            return "Code"
        if ext in set(_DOCS):
            return "Documents"
        if ext in _IMAGE_EXTS:
            return "Images"
        if ext in _ARCHIVE_EXTS:
            return "Archives"
        if ext in _MEDIA_EXTS:
            return "Media"
        return "Other"
    if mode == GroupByMode.SIZE:
        if item.is_dir:
            return "Folders"
        s = item.size
        if s < 1_024:
            return "Tiny (<1 KB)"
        if s < 1_048_576:
            return "Small (<1 MB)"
        if s < 104_857_600:
            return "Medium (<100 MB)"
        return "Large (>100 MB)"
    if mode == GroupByMode.DATE:
        if item.modified == 0.0:
            return "Unknown"
        import time
        now = time.time()
        age = now - item.modified
        if age < 86_400:
            return "Today"
        if age < 172_800:
            return "Yesterday"
        if age < 604_800:
            return "This week"
        return "Older"
    return ""


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
        self._compare_result: dict[str, str] = {}  # filename → "left_only"|"right_only"|"differs"|"same"

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

    def set_git_status(
        self,
        statuses: dict[Path, str],
        dirty_dirs: frozenset[Path],
        visible_range: tuple[int, int] | None = None,
    ) -> None:
        self._git_statuses = statuses
        self._git_dirty_dirs = dirty_dirs
        if self.rowCount():
            first, last = visible_range if visible_range is not None else (0, self.rowCount() - 1)
            self.dataChanged.emit(
                self.index(first, 0),
                self.index(last, 0),
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

    def set_compare_result(self, diff: dict[str, str]) -> None:
        """Set per-filename compare status. Drives ForegroundRole colors."""
        self._compare_result = dict(diff)
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
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
            if self._compare_result:
                status = self._compare_result.get(item.name)
                if status == "left_only":
                    return QBrush(QColor("#00cc44"))   # green
                if status == "right_only":
                    return QBrush(QColor("#cc0000"))   # red
                if status == "differs":
                    return QBrush(QColor("#ccaa00"))   # yellow
                if status == "same":
                    return None
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
        if col == COL_ATIME:
            if item.atime == 0.0:
                return ""
            return datetime.datetime.fromtimestamp(item.atime).strftime("%Y-%m-%d %H:%M")
        if col == COL_OWNER:
            return item.owner
        return None


def _scan_worker(
    vfs: object,
    path: Path,
    cancel: threading.Event,
    out_queue: queue.SimpleQueue,
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
        self._filters: list[str] = []
        self._show_hidden = False
        self._tag_filter: str | None = None
        self._tag_store: object | None = None
        self._invert: bool = False
        self._group_mode: GroupByMode = GroupByMode.NONE
        self._sort_key_cache: dict[int, str] = {}
        self._type_filter: str = "all"
        self._show_only_marked: bool = False
        self._marked_paths: set[Path] = set()

    @property
    def _filter(self) -> str:
        """Backward-compat accessor: returns first filter or empty string."""
        return self._filters[0] if self._filters else ""

    def setSourceModel(self, model: object) -> None:
        super().setSourceModel(model)  # type: ignore[arg-type]
        if model is not None:
            model.modelReset.connect(self._sort_key_cache.clear)  # type: ignore[attr-defined]

    def invalidateFilter(self) -> None:  # type: ignore[override]
        self._sort_key_cache.clear()
        super().invalidateFilter()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self._sort_key_cache.clear()
        super().sort(column, order)

    def _sort_key(self, row: int) -> str:
        if row not in self._sort_key_cache:
            model = self.sourceModel()
            item: FileItem | None = model.data(model.index(row, COL_NAME), Qt.ItemDataRole.UserRole)
            self._sort_key_cache[row] = item.name.lower() if item else ""
        return self._sort_key_cache[row]

    def set_tag_filter(self, tag: str | None, store: object | None = None) -> None:
        self._tag_filter = tag
        self._tag_store = store
        self.invalidateRowsFilter()

    def set_filter(self, text: str) -> None:
        self._filters = [text.lower()] if text else []
        self.invalidateRowsFilter()

    def push_filter(self, text: str) -> None:
        if text:
            self._filters.append(text.lower())
            self.invalidateRowsFilter()

    def pop_filter(self) -> None:
        if self._filters:
            self._filters.pop()
            self.invalidateRowsFilter()

    def set_type_filter(self, t: str) -> None:  # "all"|"files"|"dirs"
        self._type_filter = t
        self.invalidateRowsFilter()

    def set_marked_paths(self, paths: set[Path]) -> None:
        self._marked_paths = set(paths)
        if self._show_only_marked:
            self.invalidateRowsFilter()

    def set_show_only_marked(self, enabled: bool) -> None:
        self._show_only_marked = enabled
        self.invalidateRowsFilter()

    def set_show_hidden(self, show: bool) -> None:
        self._show_hidden = show
        self.invalidateRowsFilter()

    def set_invert(self, invert: bool) -> None:
        self._invert = invert
        self.invalidateRowsFilter()

    def set_group_by(self, mode: GroupByMode) -> None:
        self._group_mode = mode
        self.invalidate()

    def data(self, index: _Idx, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == GROUP_ROLE:
            src_idx = self.mapToSource(index)
            model = self.sourceModel()
            item: FileItem | None = model.data(src_idx.sibling(src_idx.row(), COL_NAME), Qt.ItemDataRole.UserRole)
            if item is None:
                return ""
            return _group_key(item, self._group_mode)
        return super().data(index, role)

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
        # F217 — type filter
        if self._type_filter == "files" and item.is_dir:
            return False
        if self._type_filter == "dirs" and not item.is_dir:
            return False
        # F284 — sticky marks
        if self._show_only_marked and item.path not in self._marked_paths:
            return False
        # F291 — stacked filters (was single _filter)
        if self._filters:
            match = all(_fuzzy_match(f, item.name) for f in self._filters)
            return (not match) if self._invert else match
        return True  # no filter → show all regardless of invert

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
        # Group-aware sort: keep group members together
        if self._group_mode != GroupByMode.NONE:
            lg = _group_key(l_item, self._group_mode)
            rg = _group_key(r_item, self._group_mode)
            if lg != rg:
                return lg < rg if asc else lg > rg
        if l_item.is_dir != r_item.is_dir:
            return l_item.is_dir if asc else r_item.is_dir
        lk = self._sort_key(left.row())
        rk = self._sort_key(right.row())
        return lk < rk if asc else lk > rk
