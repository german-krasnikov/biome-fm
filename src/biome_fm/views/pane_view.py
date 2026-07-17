"""PaneView — passive dual-pane file manager widget."""

from __future__ import annotations

import sys
from pathlib import Path

from biome_fm.models.directory_model import (
    COL_EXT,
    COL_MODIFIED,
    COL_NAME,
    COL_SIZE,
    DirectoryModel,
    DirSortFilterProxy,
)
from biome_fm.models.file_item import FileItem
from biome_fm.models.finder_tags import finder_tag_color, get_finder_tags
from biome_fm.qt import (
    QApplication,
    QColor,
    QDrag,
    QEvent,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMimeData,
    QModelIndex,
    QPen,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    Qt,
    QTableView,
    QTimer,
    QVBoxLayout,
    QWidget,
    Signal,
)

_AUTO_RESIZE_THRESHOLD = 500
from biome_fm.views.bookmark_menu import BookmarkMenu
from biome_fm.views.dnd_utils import _MIME, make_path_mime
from biome_fm.views.filter_bar import FilterBar
from biome_fm.views.jump_bar import JumpBar

_MOVE_MODS = Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.AltModifier


def _match_positions(pattern: str, text: str) -> list[int]:
    """Indices in text where fuzzy pattern chars match (subsequence)."""
    if not pattern:
        return []
    pos = []
    pi = 0
    p = pattern.lower()
    for ti, ch in enumerate(text.lower()):
        if pi < len(p) and ch == p[pi]:
            pos.append(ti)
            pi += 1
    return pos if pi == len(p) else []


class _DropHintDelegate(QStyledItemDelegate):
    """Draws highlight border around folder row during DnD hover."""

    def __init__(self, table: _PaneTableView) -> None:
        super().__init__(table)
        self._table = table
        self._filter: str = ""
        self._show_finder_tags: bool = sys.platform == "darwin"

    def set_filter(self, text: str) -> None:
        self._filter = text

    def initStyleOption(self, option: object, index: object) -> None:
        super().initStyleOption(option, index)  # type: ignore[arg-type]
        option.state &= ~QStyle.StateFlag.State_HasFocus  # type: ignore[attr-defined]
        option.state &= ~QStyle.StateFlag.State_Selected  # type: ignore[attr-defined]

    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)
        # DnD drop hint
        if index.row() == self._table._drop_hint_row:
            painter.save()
            pen = painter.pen()
            pen.setColor(option.palette.highlight().color())
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            painter.restore()
        # Cursor row border (TC-style: border around entire row, no fill)
        if self._table._cursor_row == index.row() >= 0:
            painter.save()
            pen = painter.pen()
            pen.setColor(option.palette.highlight().color())
            pen.setWidth(1)
            painter.setPen(pen)
            rect = option.rect
            painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
            painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
            if index.column() == 0:
                painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
            model = index.model()
            if model and index.column() == model.columnCount() - 1:
                painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
            painter.restore()
        # Finder tag dots (macOS only)
        if self._show_finder_tags and index.column() == COL_NAME:
            item = index.data(Qt.ItemDataRole.UserRole)
            if isinstance(item, FileItem) and item.name != "..":
                tags = get_finder_tags(item.path)
                colors = [c for t in tags if (c := finder_tag_color(t))]
                if colors:
                    painter.save()
                    painter.setPen(Qt.PenStyle.NoPen)
                    dot_x = option.rect.right() - len(colors) * 11 - 2
                    dot_y = option.rect.center().y() - 4
                    for color in colors[:4]:
                        painter.setBrush(QColor(color))
                        painter.drawEllipse(dot_x, dot_y, 8, 8)
                        dot_x += 11
                    painter.restore()
        # Filter character underlines
        if self._filter and index.column() == COL_NAME:
            name = index.data(Qt.ItemDataRole.DisplayRole) or ""
            positions = _match_positions(self._filter, name)
            if positions:
                fm = option.fontMetrics
                base_x = option.rect.left() + 4
                y = option.rect.bottom() - 2
                accent = option.palette.highlight().color()
                painter.save()
                painter.setPen(QPen(accent, 2))
                for p in positions:
                    x = base_x + fm.horizontalAdvance(name[:p])
                    w = fm.horizontalAdvance(name[p])
                    painter.drawLine(x, y, x + w, y)
                painter.restore()

    def createEditor(self, parent, option, index) -> QLineEdit | None:
        pane = self._table.parent()
        if not isinstance(pane, PaneView):
            return None
        src_idx = pane._proxy.mapToSource(index)
        item = pane._model.item_at(src_idx.row())
        if item is None or item.name == ".." or index.column() != COL_NAME:
            return None
        editor = QLineEdit(parent)
        editor.setText(item.name)
        dot = item.name.rfind(".")
        if dot > 0 and not item.is_dir:
            editor.setSelection(0, dot)
        else:
            editor.selectAll()
        return editor

    def setEditorData(self, editor, index) -> None:
        pass  # createEditor already sets text + selection

    def setModelData(self, editor, model, index) -> None:
        pane = self._table.parent()
        if not isinstance(pane, PaneView):
            return
        src_idx = pane._proxy.mapToSource(index)
        item = pane._model.item_at(src_idx.row())
        new_name = editor.text().strip()
        if item and new_name and new_name != item.name:
            pane.inline_rename_requested.emit(item, new_name)


class _PaneTableView(QTableView):
    """QTableView subclass: key routing, drag-and-drop, context menu."""

    _uniform_row_heights: bool = False
    _drop_hint_row: int = -1
    _cursor_row: int = -1
    _spring_row: int = -1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDropIndicatorShown(True)
        self.setItemDelegate(_DropHintDelegate(self))
        self._spring_timer = QTimer(self)
        self._spring_timer.setSingleShot(True)
        self._spring_timer.setInterval(800)
        self._spring_timer.timeout.connect(self._spring_navigate)

    # QTreeView compat: QTableView lacks this; Fixed row sections achieve same effect
    def setUniformRowHeights(self, uniform: bool) -> None:
        self._uniform_row_heights = uniform

    def uniformRowHeights(self) -> bool:
        return self._uniform_row_heights

    def _on_cursor_row_changed(self, current: QModelIndex, _: QModelIndex) -> None:
        self._cursor_row = current.row() if current.isValid() else -1
        self.viewport().update()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)  # must run: updates header offset + selection dirty region
        if self.property("_glass"):
            # ponytail: full repaint kills bitblt ghost pixels on translucent viewports;
            # ceiling: wastes one bitblt per scroll tick, fine for optional glass mode
            self.viewport().update()

    def event(self, event: object) -> bool:
        # Intercept Tab at event() level — before Qt's focus-traversal machinery
        # (QAbstractItemView accepts ShortcutOverride for Tab, suppressing QShortcut)
        if (hasattr(event, "type") and
                event.type() == QEvent.Type.KeyPress and  # type: ignore[attr-defined]
                hasattr(event, "key") and
                event.key() == Qt.Key.Key_Tab and  # type: ignore[attr-defined]
                not (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):  # type: ignore[attr-defined]
            ts = getattr(self.window(), "tab_shortcut", None)
            if ts is not None:
                ts.activated.emit()
            event.accept()  # type: ignore[attr-defined]
            return True
        return super().event(event)  # type: ignore[arg-type]

    def keyPressEvent(self, event: object) -> None:
        if not hasattr(event, "key"):
            super().keyPressEvent(event)  # type: ignore[arg-type]
            return
        key = event.key()
        mods = event.modifiers()  # type: ignore[attr-defined]
        parent = self.parent()
        if isinstance(parent, PaneView):
            if key == Qt.Key.Key_F2:
                idx = self.currentIndex()
                if idx.isValid():
                    self.edit(self.model().index(idx.row(), COL_NAME))
                return
            if key == Qt.Key.Key_Space:
                parent.view_requested.emit()
                return
            if key == Qt.Key.Key_Insert:
                parent.mark_toggle_requested.emit()
                return
            if key == Qt.Key.Key_Down and mods & Qt.KeyboardModifier.ShiftModifier:
                parent.mark_toggle_requested.emit()
                return
            if key == Qt.Key.Key_Up and mods & Qt.KeyboardModifier.ShiftModifier:
                parent.mark_toggle_up_requested.emit()
                return
            if key == Qt.Key.Key_Slash or (
                key == Qt.Key.Key_F and mods & Qt.KeyboardModifier.ControlModifier
            ):
                parent.filter_bar.activate()
                return
            if key == Qt.Key.Key_Backspace:
                parent.up_requested.emit()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = parent.current_item()
                if item is not None:
                    parent.item_activated.emit(item)
                return
            ctrl = Qt.KeyboardModifier.ControlModifier
            if mods & ctrl:
                if key == Qt.Key.Key_C:
                    parent.clipboard_copy_requested.emit()
                    return
                if key == Qt.Key.Key_X:
                    parent.clipboard_cut_requested.emit()
                    return
                if key == Qt.Key.Key_V:
                    parent.clipboard_paste_requested.emit()
                    return
            if key == Qt.Key.Key_Delete:
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    parent.context_action_requested.emit("delete")
                else:
                    parent.trash_requested.emit()
                return
        text = event.text()  # type: ignore[attr-defined]
        ctrl_or_alt = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        if (text and text.isprintable() and not (mods & ctrl_or_alt)
                and key != Qt.Key.Key_Space and isinstance(parent, PaneView)):
            parent.jump_bar.append_char(text)
            return
        super().keyPressEvent(event)  # type: ignore[arg-type]

    def mousePressEvent(self, event: object) -> None:
        if (hasattr(event, "modifiers") and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier and
                hasattr(event, "button") and
                event.button() == Qt.MouseButton.LeftButton):
            idx = self.indexAt(event.pos())  # type: ignore[attr-defined]
            if idx.isValid():
                self.setCurrentIndex(idx)
                pane = self.parent()
                if isinstance(pane, PaneView):
                    src = pane._proxy.mapToSource(pane._proxy.index(idx.row(), 0))
                    item = pane._model.item_at(src.row())
                    if item and item.name != "..":
                        pane.mark_at_requested.emit(item)
                return
        super().mousePressEvent(event)  # type: ignore[arg-type]

    def mimeData(self, indexes: object) -> QMimeData:
        pane = self.parent()
        paths: list[str] = []
        if isinstance(pane, PaneView):
            marked = pane._model.marks
            if marked:
                paths = [
                    str(item.path)
                    for row in range(pane._model.rowCount())
                    if (item := pane._model.item_at(row)) and item.path in marked and item.name != ".."
                ]
            else:
                rows = {idx.row() for idx in indexes}  # type: ignore[attr-defined]
                for proxy_row in rows:
                    src = pane._proxy.mapToSource(pane._proxy.index(proxy_row, 0))
                    item = pane._model.item_at(src.row())
                    if item and item.name != "..":
                        paths.append(str(item.path))
        alt = bool(paths and QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier)
        return make_path_mime(paths, urls=not alt)

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        indexes = self.selectedIndexes()
        if not indexes:
            return
        mime = self.mimeData(indexes)
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(supported_actions)

    def dragEnterEvent(self, event: object) -> None:
        if hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME):
            event.acceptProposedAction()  # type: ignore[attr-defined]
        else:
            super().dragEnterEvent(event)  # type: ignore[arg-type]

    def dragMoveEvent(self, event: object) -> None:
        if not (hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME)):
            super().dragMoveEvent(event)  # type: ignore[arg-type]
            return
        idx = self.indexAt(event.pos())  # type: ignore[attr-defined]
        pane = self.parent()
        if idx.isValid() and isinstance(pane, PaneView):
            src_idx = pane._proxy.mapToSource(pane._proxy.index(idx.row(), 0))
            item = pane._model.item_at(src_idx.row())
            self._drop_hint_row = (
                idx.row() if (item and item.is_dir and item.name != "..") else -1
            )
        else:
            self._drop_hint_row = -1
        self.viewport().update()
        # Spring-loaded: start/reset timer when hovering a new dir row
        if self._drop_hint_row != self._spring_row:
            self._spring_timer.stop()
            self._spring_row = self._drop_hint_row
            if self._spring_row >= 0:
                self._spring_timer.start()
        if event.modifiers() & _MOVE_MODS:  # type: ignore[attr-defined]
            event.setDropAction(Qt.DropAction.MoveAction)  # type: ignore[attr-defined]
        else:
            event.setDropAction(Qt.DropAction.CopyAction)  # type: ignore[attr-defined]
        event.accept()  # type: ignore[attr-defined]

    def dragLeaveEvent(self, event: object) -> None:
        self._spring_timer.stop()
        self._spring_row = -1
        self._drop_hint_row = -1
        self.viewport().update()
        super().dragLeaveEvent(event)  # type: ignore[arg-type]

    def _spring_navigate(self) -> None:
        pane = self.parent()
        if isinstance(pane, PaneView) and self._spring_row >= 0:
            src_idx = pane._proxy.mapToSource(pane._proxy.index(self._spring_row, 0))
            item = pane._model.item_at(src_idx.row())
            if item and item.is_dir:
                pane.item_activated.emit(item)
        self._spring_row = -1

    def dropEvent(self, event: object) -> None:
        if not (hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME)):
            super().dropEvent(event)  # type: ignore[arg-type]
            return
        raw = event.mimeData().data(_MIME).data().decode()
        paths = [Path(p) for p in raw.splitlines() if p]
        move = bool(event.modifiers() & _MOVE_MODS)  # type: ignore[attr-defined]
        target_folder = None
        if self._drop_hint_row != -1:
            pane = self.parent()
            if isinstance(pane, PaneView):
                src_idx = pane._proxy.mapToSource(
                    pane._proxy.index(self._drop_hint_row, 0)
                )
                item = pane._model.item_at(src_idx.row())
                if item and item.is_dir:
                    target_folder = item.path
        self._drop_hint_row = -1
        self.viewport().update()
        event.acceptProposedAction()  # type: ignore[attr-defined]
        pane = self.parent()
        if isinstance(pane, PaneView):
            pane.files_dropped.emit(paths, move, target_folder)

    def contextMenuEvent(self, event: object) -> None:
        p = self.parent()
        if not isinstance(p, PaneView):
            return
        menu = QMenu(self.window())
        for action_name, label in [
            ("copy", "Copy\tF5"),
            ("move", "Move\tF6"),
            ("delete", "Delete\tF8"),
            ("rename", "Rename\tF2"),
        ]:
            menu.addAction(label, lambda n=action_name: p.context_action_requested.emit(n))
        menu.addAction("New File…", lambda: p.new_file_requested.emit())
        menu.addSeparator()
        menu.addAction(
            "Copy Path\tCtrl+Shift+C", lambda: p.context_action_requested.emit("copy_path")
        )
        menu.addAction("View\tF3", lambda: p.context_action_requested.emit("quick_look"))
        finder_label = "Open in Finder" if sys.platform == "darwin" else "Open in File Manager"
        menu.addAction(finder_label, lambda: p.context_action_requested.emit("open_finder"))
        menu.addAction("Open Terminal Here\tF9", lambda: p.context_action_requested.emit("open_terminal"))
        menu.addAction("Checksum...", lambda: p.context_action_requested.emit("checksum"))
        menu.addSeparator()
        if p._model.marks:
            menu.addAction("Batch Rename...", lambda: p.context_action_requested.emit("batch_rename"))
        menu.addAction("Compress...", lambda: p.context_action_requested.emit("compress"))
        item = p.current_cursor_item()
        if item and not item.is_dir:
            suffixes = "".join(item.path.suffixes).lower()
            if any(suffixes.endswith(e) for e in (".zip", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz")):
                menu.addAction("Extract Here", lambda: p.context_action_requested.emit("extract"))
        menu.addSeparator()
        menu.addAction("Add to Bookmarks", lambda: p.context_action_requested.emit("add_bookmark"))
        menu.addAction("Tag Files…", lambda: p.tag_requested.emit())
        menu.addAction("AI Rename Suggestions…", lambda: p.ai_rename_requested.emit())
        # AI Actions submenu
        from biome_fm.ai.context_actions import builtin_actions
        ai_menu = menu.addMenu("AI Actions")
        cursor_item = p.current_cursor_item()
        if cursor_item and not cursor_item.is_dir:
            ext = cursor_item.path.suffix
            for label, _action_id in builtin_actions(ext):
                ai_menu.addAction(label)
            ai_menu.addSeparator()
        ai_menu.addAction("Ask AI…", lambda: p.ai_context_requested.emit())
        # Plugin extra actions
        if p.plugin_menu_extra is not None:
            extras = p.plugin_menu_extra()
            if extras:
                menu.addSeparator()
                for spec in extras:
                    if getattr(spec, "separator_before", False):
                        menu.addSeparator()
                    menu.addAction(spec.label, spec.callback)
        if p._git_status_fn is not None:
            item = p.current_cursor_item()
            if item and item.name != "..":
                xy = p._git_status_fn(item.path)
                if xy is not None:
                    menu.addSeparator()
                    if xy[1] not in (" ",) or xy == "??":  # working tree dirty or untracked
                        act = menu.addAction("Git: Stage")
                        act.triggered.connect(lambda _, i=item: p.git_stage_requested.emit(i))
                    if xy[0] not in (" ", "?"):  # staged changes
                        act = menu.addAction("Git: Unstage")
                        act.triggered.connect(lambda _, i=item: p.git_unstage_requested.emit(i))
        menu.exec(event.globalPos())  # type: ignore[attr-defined]


class PaneView(QWidget):
    item_activated = Signal(object)           # FileItem
    path_change_requested = Signal(object)    # Path
    mark_toggle_requested = Signal()
    view_requested = Signal()               # Space — Quick Look preview
    mark_toggle_up_requested = Signal()     # Shift+Up — mark + retreat cursor
    mark_at_requested = Signal(object)     # FileItem — Cmd/Ctrl+Click mark toggle
    back_requested = Signal()
    forward_requested = Signal()
    up_requested = Signal()
    home_requested = Signal()
    files_dropped = Signal(list, bool, object)  # [Path], move: bool, target_folder: Path|None
    context_action_requested = Signal(str)    # "copy"|"move"|"delete"|"rename"
    bookmark_chosen = Signal(object)          # Path
    edit_bookmarks_requested = Signal()
    cursor_changed = Signal(object)           # FileItem | None
    new_tab_requested = Signal()
    path_updated = Signal(object)              # Path — emitted after set_path()
    git_stage_requested = Signal(object)       # FileItem
    git_unstage_requested = Signal(object)     # FileItem
    inline_rename_requested = Signal(object, str)  # FileItem, new_name
    tag_requested = Signal()
    ai_rename_requested = Signal()
    ai_context_requested = Signal()
    new_file_requested = Signal()
    clipboard_copy_requested = Signal()
    clipboard_cut_requested = Signal()
    clipboard_paste_requested = Signal()
    trash_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = DirectoryModel(self)
        self._proxy = DirSortFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self.plugin_menu_extra = None  # Callable[[], list[ActionSpec]] — set by app.py
        self._git_status_fn = None  # Callable[[Path], str | None] — set by app.py
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)
        _SP = QStyle.StandardPixmap
        for sp, signal, name, tip in [
            (_SP.SP_ArrowBack, self.back_requested, "nav_back", "Back (Alt+Left / Alt+[)"),
            (_SP.SP_ArrowForward, self.forward_requested, "nav_forward", "Forward (Alt+Right / Alt+])"),
            (_SP.SP_ArrowUp, self.up_requested, "nav_up", "Up (Alt+Up)"),
        ]:
            btn = QPushButton()
            btn.setObjectName(name)
            btn.setIcon(self.style().standardIcon(sp))
            btn.setFixedWidth(28)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setToolTip(tip)
            btn.clicked.connect(signal)
            nav_layout.addWidget(btn)

        self._bookmark_menu = BookmarkMenu(self)
        self._bookmark_menu.bookmark_chosen.connect(self.bookmark_chosen)
        self._bookmark_menu.edit_requested.connect(self.edit_bookmarks_requested)
        nav_layout.addWidget(self._bookmark_menu)

        from biome_fm.views.breadcrumb_bar import BreadcrumbBar
        self._path_bar = BreadcrumbBar(self)
        self._path_bar.path_entered.connect(self._on_path_entered_text)
        nav_layout.addWidget(self._path_bar, 1)

        self._btn_new_tab = QPushButton("+")
        self._btn_new_tab.setFixedWidth(28)
        self._btn_new_tab.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_new_tab.setToolTip("New tab (Ctrl+T)")
        self._btn_new_tab.clicked.connect(self.new_tab_requested)
        nav_layout.addWidget(self._btn_new_tab)

        layout.addWidget(nav)

        self.filter_bar = FilterBar(self)
        self.filter_bar.filter_changed.connect(self._proxy.set_filter)
        self.filter_bar.closed.connect(lambda: self._proxy.set_filter(""))
        layout.addWidget(self.filter_bar)

        self._table = _PaneTableView(self)
        self._table.setAccessibleName("File list")
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setUniformRowHeights(True)

        vh = self._table.verticalHeader()
        vh.setVisible(False)
        vh.setDefaultSectionSize(22)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        for col in (COL_SIZE, COL_MODIFIED, COL_EXT):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(COL_SIZE, 70)
        self._table.setColumnWidth(COL_MODIFIED, 130)
        self._table.setColumnWidth(COL_EXT, 45)

        self._table.setSortingEnabled(True)
        self._table.activated.connect(self._on_activated)
        self._table.selectionModel().currentChanged.connect(self._on_cursor_changed)
        self._table.selectionModel().currentChanged.connect(self._table._on_cursor_row_changed)
        layout.addWidget(self._table)

        _delegate = self._table.itemDelegate()
        self.filter_bar.filter_changed.connect(_delegate.set_filter)
        self.filter_bar.closed.connect(lambda: _delegate.set_filter(""))

        self._proxy.sort(COL_NAME, Qt.SortOrder.AscendingOrder)

        self._status_label = QLabel()
        layout.addWidget(self._status_label)

        self.jump_bar = JumpBar(self)
        self.jump_bar.jump_text_changed.connect(self._on_jump)
        layout.addWidget(self.jump_bar)

    def set_bookmark_store(self, store) -> None:
        self._bookmark_menu.set_store(store)

    def set_tag_store(self, store: object | None) -> None:
        self._model.set_tag_store(store)

    _COL_MAP = {"Size": COL_SIZE, "Modified": COL_MODIFIED, "Ext": COL_EXT}

    def set_hidden_columns(self, names: list[str]) -> None:
        hh = self._table.horizontalHeader()
        for col_name, col_idx in self._COL_MAP.items():
            hh.setSectionHidden(col_idx, col_name in names)

    def set_items(self, items: list[FileItem], **kwargs: object) -> None:
        if kwargs.get("preserve_scroll"):
            vbar = self._table.verticalScrollBar()
            scroll_pos = vbar.value()
            self._model.set_items(items)
            vbar.setValue(scroll_pos)
        else:
            self._model.set_items(items)
        if len(items) <= _AUTO_RESIZE_THRESHOLD:
            self._table.horizontalHeader().resizeSections(QHeaderView.ResizeMode.ResizeToContents)

    def set_path(self, path: Path) -> None:
        self._path_bar.set_path(path)
        self.path_updated.emit(path)

    def show_error(self, message: str) -> None:
        self._path_bar.show_error(message)

    def set_nav_history(self, paths: list[Path]) -> None:
        self._path_bar.set_nav_history(paths)

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def set_marked(self, paths: set[Path]) -> None:
        self._model.set_marks(paths)

    def current_cursor_item(self) -> FileItem | None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            return None
        return self._model.item_at(self._proxy.mapToSource(idx).row())

    def advance_cursor(self) -> None:
        idx = self._table.currentIndex()
        if idx.isValid():
            nxt = idx.row() + 1
            if nxt < self._proxy.rowCount():
                self._table.setCurrentIndex(self._proxy.index(nxt, idx.column()))

    def retreat_cursor(self) -> None:
        idx = self._table.currentIndex()
        if idx.isValid() and idx.row() > 0:
            self._table.setCurrentIndex(self._proxy.index(idx.row() - 1, idx.column()))

    def set_filter_visible(self, visible: bool) -> None:
        if visible:
            self.filter_bar.activate()
        else:
            self.filter_bar.deactivate()

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

    def _on_jump(self, text: str) -> None:
        text_lower = text.lower()
        for row in range(self._proxy.rowCount()):
            idx = self._proxy.index(row, 0)
            src = self._proxy.mapToSource(idx)
            item = self._model.item_at(src.row())
            if item and item.name.lower().startswith(text_lower):
                self._table.setCurrentIndex(idx)
                return

    def _on_cursor_changed(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if current.isValid():
            src = self._proxy.mapToSource(current)
            item = self._model.item_at(src.row())
        else:
            item = None
        self.cursor_changed.emit(item)

    def _on_activated(self, proxy_index: QModelIndex) -> None:
        src = self._proxy.mapToSource(proxy_index)
        item = self._model.item_at(src.row())
        if item is not None:
            self.item_activated.emit(item)

    def select_item(self, name: str) -> None:
        for row in range(self._proxy.rowCount()):
            idx = self._proxy.index(row, 0)
            src = self._proxy.mapToSource(idx)
            item = self._model.item_at(src.row())
            if item and item.name == name:
                self._table.setCurrentIndex(idx)
                self._table.scrollTo(idx)
                return

    def get_view_state(self):
        from biome_fm.models.view_state import ViewState
        return ViewState(
            sort_col=self._proxy.sortColumn(),
            sort_asc=self._proxy.sortOrder() == Qt.SortOrder.AscendingOrder,
            filter=self._proxy._filter,
        )

    def set_filter_text(self, text: str) -> None:
        self.filter_bar.set_text(text)

    def set_view_state(self, state) -> None:
        order = Qt.SortOrder.AscendingOrder if state.sort_asc else Qt.SortOrder.DescendingOrder
        self._table.sortByColumn(state.sort_col, order)
        if state.filter:
            self._proxy.set_filter(state.filter)
            self.filter_bar.set_text(state.filter)
            self.set_filter_visible(True)
        else:
            self._proxy.set_filter("")

    def _on_path_entered_text(self, text: str) -> None:
        self.path_change_requested.emit(Path(text))
