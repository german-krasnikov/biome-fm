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
from biome_fm.qt import (
    QApplication,
    QDrag,
    QEvent,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMimeData,
    QModelIndex,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    Qt,
    QTableView,
    QUrl,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views.bookmark_menu import BookmarkMenu
from biome_fm.views.filter_bar import FilterBar
from biome_fm.views.jump_bar import JumpBar

_MIME = "application/x-biome-fm-paths"
_MOVE_MODS = Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.AltModifier


class _DropHintDelegate(QStyledItemDelegate):
    """Draws highlight border around folder row during DnD hover."""

    def __init__(self, table: _PaneTableView) -> None:
        super().__init__(table)
        self._table = table

    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)
        if index.row() == self._table._drop_hint_row:
            painter.save()
            pen = painter.pen()
            pen.setColor(option.palette.highlight().color())
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
            painter.restore()


class _PaneTableView(QTableView):
    """QTableView subclass: key routing, drag-and-drop, context menu."""

    _uniform_row_heights: bool = False
    _drop_hint_row: int = -1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDropIndicatorShown(True)
        self.setItemDelegate(_DropHintDelegate(self))

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        if self.property("_glass"):
            self.viewport().update()
        else:
            super().scrollContentsBy(dx, dy)

    # QTreeView compat: QTableView lacks this; Fixed row sections achieve same effect
    def setUniformRowHeights(self, uniform: bool) -> None:
        self._uniform_row_heights = uniform

    def uniformRowHeights(self) -> bool:
        return self._uniform_row_heights

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
            if key == Qt.Key.Key_Space:
                parent.view_requested.emit()
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
        text = event.text()  # type: ignore[attr-defined]
        ctrl_or_alt = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        if (text and text.isprintable() and not (mods & ctrl_or_alt)
                and key != Qt.Key.Key_Space and isinstance(parent, PaneView)):
            parent.jump_bar.append_char(text)
            return
        super().keyPressEvent(event)  # type: ignore[arg-type]

    def mimeData(self, indexes: object) -> QMimeData:
        pane = self.parent()
        rows = {idx.row() for idx in indexes}  # type: ignore[attr-defined]
        paths = []
        for proxy_row in rows:
            if isinstance(pane, PaneView):
                src = pane._proxy.mapToSource(pane._proxy.index(proxy_row, 0))
                item = pane._model.item_at(src.row())
                if item and item.name != "..":
                    paths.append(str(item.path))
        mime = QMimeData()
        mime.setData(_MIME, "\n".join(paths).encode())
        if paths:
            alt = QApplication.keyboardModifiers() & Qt.KeyboardModifier.AltModifier
            if not alt:
                mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
            mime.setText("\n".join(paths))
        return mime

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
        if event.modifiers() & _MOVE_MODS:  # type: ignore[attr-defined]
            event.setDropAction(Qt.DropAction.MoveAction)  # type: ignore[attr-defined]
        else:
            event.setDropAction(Qt.DropAction.CopyAction)  # type: ignore[attr-defined]
        event.accept()  # type: ignore[attr-defined]

    def dragLeaveEvent(self, event: object) -> None:
        self._drop_hint_row = -1
        self.viewport().update()
        super().dragLeaveEvent(event)  # type: ignore[arg-type]

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
        menu = QMenu(self)
        for action_name, label in [
            ("copy", "Copy\tF5"),
            ("move", "Move\tF6"),
            ("delete", "Delete\tF8"),
            ("rename", "Rename\tF9"),
        ]:
            menu.addAction(label, lambda n=action_name: p.context_action_requested.emit(n))
        menu.addSeparator()
        menu.addAction(
            "Copy Path\tCtrl+Shift+C", lambda: p.context_action_requested.emit("copy_path")
        )
        menu.addAction("View\tF3", lambda: p.context_action_requested.emit("quick_look"))
        finder_label = "Open in Finder" if sys.platform == "darwin" else "Open in File Manager"
        menu.addAction(finder_label, lambda: p.context_action_requested.emit("open_finder"))
        menu.addSeparator()
        menu.addAction("Add to Bookmarks", lambda: p.context_action_requested.emit("add_bookmark"))
        # Plugin extra actions
        if p.plugin_menu_extra is not None:
            extras = p.plugin_menu_extra()
            if extras:
                menu.addSeparator()
                for spec in extras:
                    if getattr(spec, "separator_before", False):
                        menu.addSeparator()
                    menu.addAction(spec.label, spec.callback)
        menu.exec(event.globalPos())  # type: ignore[attr-defined]


class PaneView(QWidget):
    item_activated = Signal(object)           # FileItem
    path_change_requested = Signal(object)    # Path
    mark_toggle_requested = Signal()
    view_requested = Signal()               # Space — Quick Look preview
    mark_toggle_up_requested = Signal()     # Shift+Up — mark + retreat cursor
    back_requested = Signal()
    forward_requested = Signal()
    up_requested = Signal()
    home_requested = Signal()
    files_dropped = Signal(list, bool, object)  # [Path], move: bool, target_folder: Path|None
    context_action_requested = Signal(str)    # "copy"|"move"|"delete"|"rename"
    bookmark_chosen = Signal(object)          # Path
    edit_bookmarks_requested = Signal()
    cursor_changed = Signal(object)           # FileItem | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = DirectoryModel(self)
        self._proxy = DirSortFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self.plugin_menu_extra = None  # Callable[[], list[ActionSpec]] — set by app.py
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
            (_SP.SP_DirHomeIcon, self.home_requested, "nav_home", "Home (Alt+Home)"),
        ]:
            btn = QPushButton()
            btn.setObjectName(name)
            btn.setIcon(self.style().standardIcon(sp))
            btn.setFixedWidth(28)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setToolTip(tip)
            btn.clicked.connect(signal)
            nav_layout.addWidget(btn)

        from biome_fm.views.breadcrumb_bar import BreadcrumbBar
        self._path_bar = BreadcrumbBar(self)
        self._path_bar.path_entered.connect(self._on_path_entered_text)
        self._path_bar.back_requested.connect(self.back_requested)
        self._path_bar.forward_requested.connect(self.forward_requested)
        nav_layout.addWidget(self._path_bar, 1)

        self._bookmark_menu = BookmarkMenu(self)
        self._bookmark_menu.bookmark_chosen.connect(self.bookmark_chosen)
        self._bookmark_menu.edit_requested.connect(self.edit_bookmarks_requested)
        nav_layout.addWidget(self._bookmark_menu)

        layout.addWidget(nav)

        self.filter_bar = FilterBar(self)
        self.filter_bar.filter_changed.connect(self._proxy.set_filter)
        self.filter_bar.closed.connect(lambda: self._proxy.set_filter(""))
        layout.addWidget(self.filter_bar)

        self._table = _PaneTableView(self)
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
        layout.addWidget(self._table)

        self._proxy.sort(COL_NAME, Qt.SortOrder.AscendingOrder)

        self._status_label = QLabel()
        layout.addWidget(self._status_label)

        self.jump_bar = JumpBar(self)
        self.jump_bar.jump_text_changed.connect(self._on_jump)
        layout.addWidget(self.jump_bar)

    def set_bookmark_store(self, store) -> None:
        self._bookmark_menu.set_store(store)

    def set_items(self, items: list[FileItem]) -> None:
        self._model.set_items(items)

    def set_path(self, path: Path) -> None:
        self._path_bar.set_path(path)

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

    def _on_path_entered_text(self, text: str) -> None:
        self.path_change_requested.emit(Path(text))
