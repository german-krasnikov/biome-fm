"""Plastic SCM Qt model classes and UI helpers — extracted from _window.py."""
from __future__ import annotations

import html
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractItemModel, QAbstractTableModel, QModelIndex, QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QPainter,
    QPalette,
    QPen,
    QStandardItem,
    QStandardItemModel,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ._models import (
    AclEntry, Attribute, BlameLine, Branch, Changeset, ConfigEntry, CSDiffFile,
    GroupInfo, Label, PlasticItem, RepoEntry, Review, Revision, Shelve, Trigger,
    UserInfo, WorkspaceEntry, Xlink,
)

_DT_FMT = "%Y-%m-%d %H:%M"
_DT_SHORT = "%b %d, %H:%M"


# ── Base table model ──────────────────────────────────────────────────────────

class _BaseModel(QAbstractTableModel):
    _HEADERS: tuple[str, ...] = ()

    def __init__(self) -> None:
        super().__init__()
        self._items: list[Any] = []

    def reset(self, items: list) -> None:  # type: ignore[override]
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def item_at(self, row: int) -> Any | None:
        return self._items[row] if 0 <= row < len(self._items) else None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._HEADERS[section] if section < len(self._HEADERS) else None
        return None


# ── Concrete table models ─────────────────────────────────────────────────────

class ChangesetModel(_BaseModel):
    _HEADERS = ("", "CS#", "Creation date", "Created by", "Comment", "Branch")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        item: Changeset = self._items[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.UserRole and col == 0:
            return item.cs_id  # for GraphDelegate lookup
        if role == Qt.ItemDataRole.ToolTipRole:
            match col:
                case 2: return item.date.strftime(_DT_FMT)
                case 3: return item.owner
                case 4: return item.comment
                case 5: return item.branch
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        match col:
            case 0: return None        # graph — delegate handles painting
            case 1: return f"CS#{item.cs_id}"
            case 2: return item.date.strftime(_DT_SHORT)
            case 3: return item.owner
            case 4: return item.comment
            case 5: return item.branch
        return None


_GRAPH_COLORS = [
    QColor(66, 133, 244), QColor(219, 68, 55), QColor(244, 180, 0),
    QColor(15, 157, 88), QColor(171, 71, 188), QColor(255, 112, 67),
    QColor(0, 172, 193), QColor(124, 179, 66),
]
_LANE_W = 16
_DOT_R = 4


class GraphDelegate(QStyledItemDelegate):
    """Paints the commit graph column: vertical lane lines + a dot per CS."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: dict[int, Any] = {}  # cs_id → CSGraphRow

    def set_rows(self, rows: list) -> None:
        self._rows = {r.cs_id: r for r in rows}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        cs_id = index.data(Qt.ItemDataRole.UserRole)
        if cs_id is None or cs_id not in self._rows:
            return
        gr = self._rows[cs_id]
        rect = option.rect
        cy = rect.center().y()

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for lane in sorted(gr.active_lanes):
            x = rect.left() + lane * _LANE_W + _LANE_W // 2
            color = _GRAPH_COLORS[lane % len(_GRAPH_COLORS)]
            painter.setPen(QPen(color, 2))
            if lane == gr.lane:
                painter.drawLine(x, rect.top(), x, cy - _DOT_R - 1)
                painter.drawLine(x, cy + _DOT_R + 1, x, rect.bottom())
            else:
                painter.drawLine(x, rect.top(), x, rect.bottom())

        cx = rect.left() + gr.lane * _LANE_W + _LANE_W // 2
        color = _GRAPH_COLORS[gr.color_idx]
        painter.setPen(QPen(color.darker(130), 1.5))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(cx - _DOT_R, cy - _DOT_R, _DOT_R * 2, _DOT_R * 2)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        if not self._rows:
            return QSize(_LANE_W, max(option.rect.height(), 26))
        max_lane = max(r.lane for r in self._rows.values()) + 1
        return QSize(max_lane * _LANE_W + _LANE_W, max(option.rect.height(), 26))


class BranchTreeModel:
    """QStandardItemModel tree grouped by '/' prefix. Branch stored in UserRole on leaves."""

    UserRole = Qt.ItemDataRole.UserRole

    def __init__(self) -> None:
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Owner", "Date"])
        self._current: str = ""
        self._branches: list[Branch] = []

    def reset(self, branches: list[Branch]) -> None:
        self._branches = branches
        self._rebuild()

    def set_current(self, name: str) -> None:
        self._current = name
        self._rebuild()

    def branch_at(self, index: QModelIndex) -> Branch | None:
        item = self.model.itemFromIndex(index)
        return item.data(self.UserRole) if item else None  # type: ignore[return-value]

    def _rebuild(self) -> None:
        self.model.removeRows(0, self.model.rowCount())
        groups: dict[str, list[Branch]] = {}
        for br in self._branches:
            prefix = br.name.rsplit("/", 1)[0] if "/" in br.name else ""
            groups.setdefault(prefix, []).append(br)

        for prefix in sorted(groups):
            label = prefix if prefix else "(root)"
            group_item = QStandardItem(label)
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            f = group_item.font(); f.setBold(True); group_item.setFont(f)

            for br in sorted(groups[prefix], key=lambda b: b.name):
                short = br.name.rsplit("/", 1)[-1]
                leaf = QStandardItem(short)
                leaf.setData(br, self.UserRole)
                leaf.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                if br.name == self._current:
                    f2 = leaf.font(); f2.setBold(True); leaf.setFont(f2)
                    leaf.setForeground(QBrush(QColor(30, 140, 60)))
                    leaf.setToolTip(f"{br.name} (current)")
                else:
                    leaf.setToolTip(br.name)
                owner_item = QStandardItem(br.owner)
                owner_item.setToolTip(br.owner)
                date_item = QStandardItem(br.date.strftime(_DT_FMT))
                date_item.setToolTip(br.date.strftime(_DT_FMT))
                group_item.appendRow([leaf, owner_item, date_item])
            self.model.appendRow(group_item)


class LabelModel(_BaseModel):
    _HEADERS = ("Name", "Changeset", "Creation date")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Label = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return f"CS#{item.changeset}"
            case 2: return item.date.strftime(_DT_FMT)
        return None


class ShelveModel(_BaseModel):
    _HEADERS = ("ID", "Date", "Owner", "Comment")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Shelve = self._items[index.row()]
        match index.column():
            case 0: return f"#{item.shelve_id}"
            case 1: return item.date.strftime(_DT_FMT)
            case 2: return item.owner
            case 3: return item.comment
        return None


_CS_STATUS_COLOR = {
    "A": QColor(0, 150, 60),
    "D": QColor(180, 0, 0),
    "M": QColor(0, 80, 180),
    "MV": QColor(140, 60, 180),
}


class CSDiffFileModel(_BaseModel):
    _HEADERS = ("St", "Path", "+", "−")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        item: CSDiffFile = self._items[index.row()]
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 0:
            return _CS_STATUS_COLOR.get(item.status)
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        match index.column():
            case 0: return item.status
            case 1: return item.path
            case 2: return f"+{item.added}"
            case 3: return f"−{item.removed}"
        return None


class ReviewModel(_BaseModel):
    _HEADERS = ("ID", "Status", "Assignee", "Date", "Title")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Review = self._items[index.row()]
        match index.column():
            case 0: return f"#{item.review_id}"
            case 1: return item.status
            case 2: return item.assignee
            case 3: return item.date.strftime(_DT_FMT)
            case 4: return item.title
        return None


# ── Details panel — reusable across CS / Branches / Labels pages ─────────────

class _DetailsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(180)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)
        self._title = QLabel()
        f = self._title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 1)
        self._title.setFont(f)
        lay.addWidget(self._title)
        self._body = QPlainTextEdit()
        self._body.setReadOnly(True)
        lay.addWidget(self._body)

    def show_changeset(self, cs: Changeset) -> None:
        self._title.setText(f"CS#{cs.cs_id}")
        self._body.setPlainText(
            f"Author:   {cs.owner}\n"
            f"Date:     {cs.date.strftime(_DT_FMT)}\n"
            f"Branch:   {cs.branch}\n\n"
            f"Comment:\n{cs.comment}"
        )

    def show_branch(self, br: Branch) -> None:
        self._title.setText(br.name)
        parent_line = f"Parent: {br.parent}\n" if br.parent else ""
        self._body.setPlainText(
            f"Owner:  {br.owner}\n"
            f"Date:   {br.date.strftime(_DT_FMT)}\n"
            f"{parent_line}"
        )

    def show_label(self, lbl: Label) -> None:
        self._title.setText(lbl.name)
        self._body.setPlainText(
            f"Changeset:  CS#{lbl.changeset}\n"
            f"Date:       {lbl.date.strftime(_DT_FMT)}"
        )

    def show_shelve(self, s: Shelve) -> None:
        self._title.setText(f"Shelve #{s.shelve_id}")
        self._body.setPlainText(
            f"Owner:    {s.owner}\n"
            f"Date:     {s.date.strftime(_DT_FMT)}\n\n"
            f"Comment:\n{s.comment}"
        )

    def show_review(self, r: Review) -> None:
        self._title.setText(f"Review #{r.review_id}")
        self._body.setPlainText(
            f"Title:    {r.title}\n"
            f"Status:   {r.status}\n"
            f"Assignee: {r.assignee}\n"
            f"Date:     {r.date.strftime(_DT_FMT)}"
        )

    def clear(self) -> None:
        self._title.clear()
        self._body.clear()


class CSDetailWidget(QWidget):
    """Bottom pane for Changesets — metadata + file list + inline diff preview."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        lay.addWidget(self._stack)

        # Page 0: placeholder
        ph = QLabel("Select a changeset to view details")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet("color: #5C6370; font-size: 13px;")
        self._stack.addWidget(ph)

        # Page 1: content
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)

        self._meta = QLabel()
        self._meta.setWordWrap(True)
        content_lay.addWidget(self._meta)

        split = QSplitter(Qt.Orientation.Horizontal)
        content_lay.addWidget(split)

        self._file_model = CSDiffFileModel()
        self._file_table = QTableView()
        self._file_table.setModel(self._file_model)
        self._file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._file_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        hdr = self._file_table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Stretch)  # Path stretches
        self._file_table.verticalHeader().hide()
        self._file_table.setShowGrid(False)
        self._file_table.setAlternatingRowColors(True)
        split.addWidget(self._file_table)

        self._diff_view = QPlainTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        DiffHighlighter(self._diff_view.document())
        split.addWidget(self._diff_view)
        split.setSizes([500, 300])

        self._stack.addWidget(content)

        self._file_table.selectionModel().currentRowChanged.connect(self._on_file_selected)
        self._files: list[CSDiffFile] = []

    def load_cs(self, cs: Changeset) -> None:
        self._stack.setCurrentIndex(1)
        self._meta.setText(
            f"<b>CS#{cs.cs_id}</b>  {html.escape(cs.owner)}  ·  "
            f"{cs.date.strftime(_DT_FMT)}  ·  {html.escape(cs.branch)}"
            f"<br><i>{html.escape(cs.comment)}</i>"
        )
        self._file_model.reset([])
        self._diff_view.clear()
        self._files = []

    def load_files(self, files: list[CSDiffFile]) -> None:
        self._files = files
        self._file_model.reset(files)
        if files:
            self._file_table.selectRow(0)

    def _on_file_selected(self, current: QModelIndex, _: QModelIndex) -> None:
        row = current.row()
        if 0 <= row < len(self._files):
            self._diff_view.setPlainText(self._files[row].diff_text)

    def clear(self) -> None:
        self._stack.setCurrentIndex(0)
        self._meta.clear()
        self._file_model.reset([])
        self._diff_view.clear()
        self._files = []


# ── Status table model (flat; used by protocol tests and _status_model) ──────

class StatusModel(_BaseModel):
    _HEADERS = ("Status", "Path", "Label")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: PlasticItem = self._items[index.row()]
        match index.column():
            case 0: return item.status
            case 1: return str(item.path)
            case 2: return item.label
        return None


# ── CheckinDialog ─────────────────────────────────────────────────────────────

class CheckinDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Check In")
        self.resize(480, 220)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Comment:"))
        self._edit = QTextEdit()
        self._edit.setPlaceholderText("Enter check-in comment…")
        lay.addWidget(self._edit)
        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        lay.addWidget(bbox)

    def message(self) -> str:
        return self._edit.toPlainText().strip()


# ── MergeOptionsDialog ────────────────────────────────────────────────────────

class MergeOptionsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Merge Options")
        lay = QVBoxLayout(self)
        self._preview = QCheckBox("Preview (dry run)")
        self._semantic = QCheckBox("Semantic merge")
        self._resolve = QComboBox()
        self._resolve.addItems(["(none)", "keepsource", "keepdestination"])
        lay.addWidget(self._preview)
        lay.addWidget(self._semantic)
        lay.addWidget(QLabel("Auto-resolve:"))
        lay.addWidget(self._resolve)
        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        lay.addWidget(bbox)

    def get_options(self) -> tuple[bool, bool, str, bool]:
        # ponytail: cherrypick hardcoded False — add checkbox when cherry-pick merge is needed
        resolve = self._resolve.currentText()
        return (self._preview.isChecked(), False,
                ("" if resolve == "(none)" else resolve),
                self._semantic.isChecked())


# ── DiffHighlighter ───────────────────────────────────────────────────────────

class DiffHighlighter(QSyntaxHighlighter):
    """Colorize unified diff lines using QPalette — works with any light/dark theme."""

    def highlightBlock(self, text: str) -> None:
        if not text:
            return

        p = QApplication.palette()
        dark = p.color(QPalette.ColorRole.Base).lightness() < 128
        fmt = QTextCharFormat()

        if text.startswith("+++") or text.startswith("---"):
            fmt.setForeground(p.color(QPalette.ColorRole.PlaceholderText))

        elif text.startswith("@@"):
            fmt.setForeground(p.color(QPalette.ColorRole.Highlight))

        elif text.startswith("+"):
            fg = QColor(60, 210, 100) if dark else QColor(0, 110, 30)
            fmt.setForeground(fg)
            fmt.setBackground(QColor(fg.red(), fg.green(), fg.blue(), 28))

        elif text.startswith("-"):
            fg = QColor(255, 90, 80) if dark else QColor(170, 0, 0)
            fmt.setForeground(fg)
            fmt.setBackground(QColor(fg.red(), fg.green(), fg.blue(), 28))

        else:
            return

        self.setFormat(0, len(text), fmt)


# ── HistoryModel ─────────────────────────────────────────────────────────────

class HistoryModel(_BaseModel):
    _HEADERS = ("Rev", "CS#", "Date", "Author", "Branch", "Comment")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Revision = self._items[index.row()]
        match index.column():
            case 0: return str(item.rev_id)
            case 1: return f"CS#{item.cs_id}"
            case 2: return item.date.strftime(_DT_FMT)
            case 3: return item.owner
            case 4: return item.branch
            case 5: return item.comment
        return None


# ── HistoryDialog ─────────────────────────────────────────────────────────────

class HistoryDialog(QDialog):
    def __init__(self, path: Path, revisions: list[Revision], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"History — {path.name}")
        self.resize(780, 400)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        model = HistoryModel()
        model.reset(revisions)
        table = QTableView()
        table.setModel(model)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().hide()
        table.setShowGrid(False)
        lay.addWidget(table)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)


# ── BlameDialog ───────────────────────────────────────────────────────────────

class BlameDialog(QDialog):
    def __init__(self, path: Path, lines: list[BlameLine], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Blame — {path.name}")
        self.resize(900, 600)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        view = QPlainTextEdit()
        view.setReadOnly(True)
        view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        lay.addWidget(view)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)
        # ponytail: plain text only — color-per-author deferred; add QTextCursor block fmt when needed
        view.setPlainText("\n".join(
            f"{bl.line_no:4d} | {bl.owner:<16s} | CS#{bl.cs_id:<6d} | {bl.date.strftime('%Y-%m-%d')} | {bl.content}"
            for bl in lines
        ))


class FindResultsDialog(QDialog):
    def __init__(self, paths: list[Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Find Results — {len(paths)} file(s)")
        self.resize(600, 400)
        lay = QVBoxLayout(self)
        lst = QListWidget()
        lst.addItems([str(p) for p in paths])
        lay.addWidget(lst)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)


# ── Module-level UI helpers ───────────────────────────────────────────────────

def _btn(layout: QHBoxLayout, text: str, slot: Callable) -> QPushButton:
    b = QPushButton(text)
    b.clicked.connect(slot)
    layout.addWidget(b)
    return b


def _filter_edit() -> QLineEdit:
    e = QLineEdit()
    e.setPlaceholderText("Filter…")
    e.setClearButtonEnabled(True)
    return e


def _make_proxy(source: QAbstractItemModel) -> QSortFilterProxyModel:
    p = QSortFilterProxyModel()
    p.setSourceModel(source)
    p.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    p.setFilterKeyColumn(-1)
    return p


def _make_table(model: QAbstractItemModel) -> QTableView:
    t = QTableView()
    t.setModel(model)
    t.setAlternatingRowColors(True)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.horizontalHeader().setStretchLastSection(True)
    t.verticalHeader().hide()
    t.setShowGrid(False)
    return t


# ── 5.3 Side-by-side diff ─────────────────────────────────────────────────────

def _split_unified_diff(text: str) -> tuple[list[str], list[str]]:
    """Parse unified diff into (left_lines, right_lines).

    Context lines → both sides.
    Removed lines (-) → left only (right gets "").
    Added lines (+) → right only (left gets "").
    Skip --- / +++ / @@ header lines.
    """
    left: list[str] = []
    right: list[str] = []
    for line in text.splitlines():
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            left.append(line[1:])
            right.append("")
        elif line.startswith("+"):
            left.append("")
            right.append(line[1:])
        else:
            content = line[1:] if line.startswith(" ") else line
            left.append(content)
            right.append(content)
    return left, right


class SideBySideDiffDialog(QDialog):
    def __init__(self, diff_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Side-by-side Diff")
        self.resize(1000, 600)

        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        left_lines, right_lines = _split_unified_diff(diff_text)

        left_edit = QPlainTextEdit()
        left_edit.setReadOnly(True)
        left_edit.setFont(mono)
        left_edit.setPlainText("\n".join(left_lines))

        right_edit = QPlainTextEdit()
        right_edit.setReadOnly(True)
        right_edit.setFont(mono)
        right_edit.setPlainText("\n".join(right_lines))

        # Sync scrollbars
        left_edit.verticalScrollBar().valueChanged.connect(right_edit.verticalScrollBar().setValue)
        right_edit.verticalScrollBar().valueChanged.connect(left_edit.verticalScrollBar().setValue)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_edit)
        splitter.addWidget(right_edit)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(splitter)


# ── 5.3.1 Line-numbered diff editor ───────────────────────────────────────────

class _LineNumberArea(QWidget):
    def __init__(self, editor: "LineNumberedDiffEdit") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor._line_number_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self._editor._paint_line_numbers(event)


class LineNumberedDiffEdit(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self._line_area = _LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_width()

    def _line_number_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_width(self, _: int = 0) -> None:
        self.setViewportMargins(self._line_number_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: "QRect", dy: int) -> None:
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(cr.left(), cr.top(), self._line_number_width(), cr.height())

    def _paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_area)
        p = QApplication.palette()
        painter.fillRect(event.rect(), p.color(QPalette.ColorRole.AlternateBase))
        block = self.firstVisibleBlock()
        num = block.blockNumber() + 1
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        painter.setPen(p.color(QPalette.ColorRole.PlaceholderText))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0, top, self._line_area.width() - 4, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, str(num),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1
        painter.end()


# ── 5.3.2 Inline diff panel ────────────────────────────────────────────────────

class InlineDiffPanel(QWidget):
    """Reusable inline diff viewer — unified or side-by-side, with image fallback."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        tb = QHBoxLayout()
        tb.setSpacing(4)
        self._mode_unified = QPushButton("Unified")
        self._mode_unified.setCheckable(True)
        self._mode_unified.setChecked(True)
        self._mode_sbs = QPushButton("Side-by-Side")
        self._mode_sbs.setCheckable(True)
        self._mode_unified.clicked.connect(lambda: self._set_mode(0))
        self._mode_sbs.clicked.connect(lambda: self._set_mode(1))
        tb.addWidget(self._mode_unified)
        tb.addWidget(self._mode_sbs)
        tb.addStretch()
        self._filename_label = QLabel()
        tb.addWidget(self._filename_label)
        lay.addLayout(tb)

        self._stack = QStackedWidget()
        lay.addWidget(self._stack)

        # Page 0: unified
        self._unified_edit = LineNumberedDiffEdit()
        DiffHighlighter(self._unified_edit.document())
        self._stack.addWidget(self._unified_edit)

        # Page 1: side-by-side
        self._sbs_pane = QSplitter(Qt.Orientation.Horizontal)
        self._sbs_left = LineNumberedDiffEdit()
        self._sbs_right = LineNumberedDiffEdit()
        DiffHighlighter(self._sbs_left.document())
        DiffHighlighter(self._sbs_right.document())
        self._sbs_left.verticalScrollBar().valueChanged.connect(
            self._sbs_right.verticalScrollBar().setValue
        )
        self._sbs_right.verticalScrollBar().valueChanged.connect(
            self._sbs_left.verticalScrollBar().setValue
        )
        self._sbs_pane.addWidget(self._sbs_left)
        self._sbs_pane.addWidget(self._sbs_right)
        self._stack.addWidget(self._sbs_pane)

        # Page 2: image
        self._img_scroll = QScrollArea()
        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_scroll.setWidget(self._img_label)
        self._img_scroll.setWidgetResizable(True)
        self._stack.addWidget(self._img_scroll)

        # Page 3: binary notice
        self._binary_label = QLabel("(binary file)")
        self._binary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stack.addWidget(self._binary_label)

        # Page 4: placeholder (default)
        ph = QLabel("Select a file to preview changes")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet("color: #5C6370; font-size: 13px;")
        self._stack.addWidget(ph)

        self._stack.setCurrentIndex(4)
        self._last_diff = ""

    def _set_mode(self, idx: int) -> None:
        self._mode_unified.setChecked(idx == 0)
        self._mode_sbs.setChecked(idx == 1)
        if idx == 1 and self._last_diff:
            left, right = _split_unified_diff(self._last_diff)
            self._sbs_left.setPlainText("\n".join(left))
            self._sbs_right.setPlainText("\n".join(right))
        self._stack.setCurrentIndex(idx)

    def show_diff(self, text: str, filename: str = "") -> None:
        self._last_diff = text
        self._filename_label.setText(filename)
        self._unified_edit.setPlainText(text)
        if self._mode_sbs.isChecked():
            left, right = _split_unified_diff(text)
            self._sbs_left.setPlainText("\n".join(left))
            self._sbs_right.setPlainText("\n".join(right))
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(0)

    def show_image(self, path: Path) -> None:
        from PySide6.QtGui import QPixmap
        px = QPixmap(str(path))
        if px.isNull():
            self.show_binary(path.name)
            return
        self._img_label.setPixmap(px)
        self._filename_label.setText(path.name)
        self._stack.setCurrentIndex(2)

    def show_binary(self, filename: str = "") -> None:
        self._binary_label.setText(
            f"(binary file — {filename})" if filename else "(binary file)"
        )
        self._filename_label.setText(filename)
        self._stack.setCurrentIndex(3)

    def clear(self) -> None:
        self._unified_edit.clear()
        self._sbs_left.clear()
        self._sbs_right.clear()
        self._img_label.clear()
        self._filename_label.clear()
        self._last_diff = ""
        self._stack.setCurrentIndex(4)
        self._mode_unified.setChecked(True)
        self._mode_sbs.setChecked(False)


# ── Status icon delegate ──────────────────────────────────────────────────────

_STATUS_COLORS: dict[str, str] = {
    "CO": "#F5A623", "CH": "#F5A623",
    "AD": "#4CAF50", "PR": "#9E9E9E",
    "DE": "#F44336", "LD": "#F44336",
    "MV": "#2196F3", "CP": "#2196F3",
}

_STATUS_LETTER: dict[str, str] = {
    "CO": "M", "CH": "M",
    "AD": "A",
    "DE": "D", "LD": "D",
    "PR": "?",
    "MV": "R",
    "CP": "C",
}


class StatusIconDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):  # type: ignore[override]
        plastic = index.data(Qt.ItemDataRole.UserRole)
        if not plastic or not hasattr(plastic, "status"):
            super().paint(painter, option, index)
            return
        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, option.palette.base())
        # Letter
        color = QColor(_STATUS_COLORS.get(plastic.status, "#9E9E9E"))
        letter = _STATUS_LETTER.get(plastic.status, plastic.status[:1])
        painter.save()
        f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QPen(color))
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, letter)
        painter.restore()


# ── 5.4 Xlink table model ─────────────────────────────────────────────────────

class XlinkModel(_BaseModel):
    _HEADERS = ("Local Path", "Server", "Repository", "Branch", "CS#")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Xlink = self._items[index.row()]
        match index.column():
            case 0: return item.path
            case 1: return item.server
            case 2: return item.repo
            case 3: return item.branch
            case 4: return f"CS#{item.cs_id}" if item.cs_id else ""
        return None


# ── 5.6 Attribute table model ─────────────────────────────────────────────────

class AttributeModel(_BaseModel):
    _HEADERS = ("Name", "Value")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Attribute = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return item.value
        return None


class AttributesDialog(QDialog):
    def __init__(self, obj_spec: str, items: list[Attribute], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Attributes — {obj_spec}")
        self.resize(500, 300)
        lay = QVBoxLayout(self)
        model = AttributeModel()
        model.reset(items)
        table = _make_table(model)
        lay.addWidget(table)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)


# ── 5.7 ACL table model ───────────────────────────────────────────────────────

class AclModel(_BaseModel):
    _HEADERS = ("Principal", "Kind", "Permission")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: AclEntry = self._items[index.row()]
        match index.column():
            case 0: return item.principal
            case 1: return item.kind
            case 2: return item.permission
        return None


# ── 5.8 User / Group table models ────────────────────────────────────────────

class UserModel(_BaseModel):
    _HEADERS = ("Name", "Email")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: UserInfo = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return item.email
        return None


class GroupModel(_BaseModel):
    _HEADERS = ("Name", "Members")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: GroupInfo = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return ", ".join(item.members)
        return None


# ── Branch DAG widget (5.1) ───────────────────────────────────────────────────

class BranchDAGWidget(QGraphicsView):
    _COLORS = [
        QColor(66, 133, 244), QColor(219, 68, 55), QColor(244, 180, 0),
        QColor(15, 157, 88), QColor(171, 71, 188), QColor(255, 112, 67),
        QColor(0, 172, 193), QColor(124, 179, 66),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def load(self, nodes: list, branches: list) -> None:
        self._scene.clear()
        if not nodes:
            return
        branch_names = sorted(set(n.branch for n in nodes))
        color_map = {name: self._COLORS[i % len(self._COLORS)] for i, name in enumerate(branch_names)}

        by_branch: dict[str, list] = {}
        for n in nodes:
            by_branch.setdefault(n.branch, []).append(n)

        # Intra-branch edges
        edge_pen = QPen(QColor(180, 180, 180), 1.5)
        for branch_nodes in by_branch.values():
            for i in range(1, len(branch_nodes)):
                prev, curr = branch_nodes[i - 1], branch_nodes[i]
                self._scene.addLine(prev.x, prev.y, curr.x, curr.y, edge_pen)

        # Cross-branch edges (parent → child fork points)
        fork_pen = QPen(QColor(140, 140, 140), 1.0, Qt.PenStyle.DashLine)
        for b in branches:
            if not b.parent or b.parent not in by_branch or b.name not in by_branch:
                continue
            parent_last = by_branch[b.parent][-1]
            child_first = by_branch[b.name][0]
            self._scene.addLine(parent_last.x, parent_last.y, child_first.x, child_first.y, fork_pen)

        R = 6
        for n in nodes:
            color = color_map.get(n.branch, self._COLORS[0])
            item = self._scene.addEllipse(
                n.x - R, n.y - R, 2 * R, 2 * R,
                QPen(color.darker(120)), QBrush(color),
            )
            item.setToolTip(f"CS#{n.cs_id}\n{n.branch}\n{n.date.strftime('%Y-%m-%d %H:%M')}")


# ── Three-way merge viewer dialog (5.2) ───────────────────────────────────────

class ThreeWayMergeDialog(QDialog):
    def __init__(
        self, path: Path, base: str, source: str, dest: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"3-Way Merge — {path.name}")
        self.resize(1200, 700)
        lay = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        edits: list[QPlainTextEdit] = []
        for title, text in [("Base", base), ("Source (Theirs)", source), ("Destination (Mine)", dest)]:
            pane = QWidget()
            pane_lay = QVBoxLayout(pane)
            pane_lay.setContentsMargins(2, 2, 2, 2)
            pane_lay.addWidget(QLabel(title))
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            edit.setFont(fixed)
            edit.setPlainText(text)
            pane_lay.addWidget(edit)
            splitter.addWidget(pane)
            edits.append(edit)
        for i, src in enumerate(edits):
            for j, dst in enumerate(edits):
                if i != j:
                    src.verticalScrollBar().valueChanged.connect(dst.verticalScrollBar().setValue)
        lay.addWidget(splitter)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)


# ── Preferences: cm config model (#8) ─────────────────────────────────────────

class ConfigModel(_BaseModel):
    _HEADERS = ("Key", "Value")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        entry: ConfigEntry = self._items[index.row()]
        match index.column():
            case 0: return entry.key
            case 1: return entry.value
        return None


# ── .conf file editor dialog (#2 / #3) ────────────────────────────────────────

# ── Workspace & Repo models (#1) ─────────────────────────────────────────────

class WorkspaceModel(_BaseModel):
    _HEADERS = ("Name", "Path", "Server")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: WorkspaceEntry = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return str(item.path)
            case 2: return item.server
        return None


class RepoModel(_BaseModel):
    _HEADERS = ("Name", "Server")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: RepoEntry = self._items[index.row()]
        match index.column():
            case 0: return item.name
            case 1: return item.server
        return None


# ── Trigger model (#6) ────────────────────────────────────────────────────────

class TriggerModel(_BaseModel):
    _HEADERS = ("ID", "Name", "Event", "Filter", "Command")

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item: Trigger = self._items[index.row()]
        match index.column():
            case 0: return item.trigger_id
            case 1: return item.name
            case 2: return item.event
            case 3: return item.filter
            case 4: return item.command
        return None


class ConfEditorDialog(QDialog):
    def __init__(self, title: str, path: Path, parent: QWidget | None = None) -> None:
        from ._conf_files import read_conf
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        lay = QVBoxLayout(self)
        self._edit = QPlainTextEdit(read_conf(path))
        lay.addWidget(self._edit)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def text(self) -> str:
        return self._edit.toPlainText()
