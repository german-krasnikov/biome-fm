"""DirectoryModel -- thin QAbstractTableModel adapter over list[FileItem]."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from biome_fm.models.file_item import FileItem
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

_Idx = QModelIndex | QPersistentModelIndex


class DirectoryModel(QAbstractTableModel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[FileItem] = []
        self._marks: set[Path] = set()

    def set_items(self, items: list[FileItem]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def item_at(self, row: int) -> FileItem | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def flags(self, index: _Idx) -> Qt.ItemFlag:
        base = super().flags(index)
        if not index.isValid():
            return base
        if self._items[index.row()].name != "..":
            base |= Qt.ItemFlag.ItemIsDragEnabled
        return base | Qt.ItemFlag.ItemIsDropEnabled

    def set_marks(self, paths: set[Path]) -> None:
        self._marks = set(paths)
        if self._items:
            top = self.index(0, 0)
            bot = self.index(len(self._items) - 1, self.columnCount() - 1)
            self.dataChanged.emit(top, bot, [Qt.ItemDataRole.BackgroundRole])

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
            if item.name == ".." or item.is_dir:
                return None
            if item.name.startswith("."):
                return QBrush(QColor(_DIM))
            ext = Path(item.name).suffix.lower()
            color = _EXT_COLORS.get(ext)
            return QBrush(QColor(color)) if color else None
        if role == Qt.ItemDataRole.ToolTipRole:
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
            return item.size_str
        if col == COL_MODIFIED:
            if item.modified == 0.0:
                return ""
            return datetime.datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M")
        if col == COL_EXT:
            return Path(item.name).suffix.lstrip(".") if not item.is_dir else ""
        return None


class DirSortFilterProxy(QSortFilterProxyModel):
    """Keeps '..' pinned first, dirs before files, then default sort."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._filter = ""

    def set_filter(self, text: str) -> None:
        self._filter = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: _Idx) -> bool:
        if not self._filter:
            return True
        _role = Qt.ItemDataRole.UserRole
        model = self.sourceModel()
        item: FileItem | None = model.data(model.index(source_row, COL_NAME), _role)
        if item is None or item.name == "..":
            return True
        return self._filter in item.name.lower()

    def lessThan(self, left: _Idx, right: _Idx) -> bool:
        _role = Qt.ItemDataRole.UserRole
        model = self.sourceModel()
        l_item: FileItem | None = model.data(left.sibling(left.row(), COL_NAME), _role)
        r_item: FileItem | None = model.data(right.sibling(right.row(), COL_NAME), _role)
        if l_item is None or r_item is None:
            return super().lessThan(left, right)
        if l_item.name == "..":
            return True
        if r_item.name == "..":
            return False
        if l_item.is_dir != r_item.is_dir:
            return l_item.is_dir
        return super().lessThan(left, right)
