"""PaneView — passive dual-pane file manager widget."""

from __future__ import annotations

from pathlib import Path

from biome_fm.models.directory_model import COL_NAME, DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem
from biome_fm.qt import (
    QDrag,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMimeData,
    QModelIndex,
    QPushButton,
    Qt,
    QTableView,
    QVBoxLayout,
    QWidget,
    Signal,
)

_MIME = "application/x-biome-fm-paths"


class _PaneTableView(QTableView):
    """QTableView subclass: Space for mark toggle, drag-and-drop, context menu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDropIndicatorShown(True)

    def keyPressEvent(self, event: object) -> None:  # type: ignore[override]
        if hasattr(event, "key") and event.key() == Qt.Key.Key_Space:  # type: ignore[union-attr]
            parent = self.parent()
            if isinstance(parent, PaneView):
                parent.mark_toggle_requested.emit()
                return
        super().keyPressEvent(event)  # type: ignore[arg-type]

    def mimeData(self, indexes: object) -> QMimeData:  # type: ignore[override]
        pane = self.parent()
        rows = {idx.row() for idx in indexes}  # type: ignore[union-attr]
        paths = []
        for proxy_row in rows:
            if isinstance(pane, PaneView):
                src = pane._proxy.mapToSource(pane._proxy.index(proxy_row, 0))
                item = pane._model.item_at(src.row())
                if item and item.name != "..":
                    paths.append(str(item.path))
        mime = QMimeData()
        mime.setData(_MIME, "\n".join(paths).encode())
        return mime

    def startDrag(self, supported_actions: Qt.DropAction) -> None:  # type: ignore[override]
        indexes = self.selectedIndexes()
        if not indexes:
            return
        mime = self.mimeData(indexes)
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(supported_actions)

    def dragEnterEvent(self, event: object) -> None:  # type: ignore[override]
        if hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME):  # type: ignore[union-attr]
            event.acceptProposedAction()  # type: ignore[union-attr]
        else:
            super().dragEnterEvent(event)  # type: ignore[arg-type]

    def dragMoveEvent(self, event: object) -> None:  # type: ignore[override]
        if hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME):  # type: ignore[union-attr]
            event.acceptProposedAction()  # type: ignore[union-attr]
        else:
            super().dragMoveEvent(event)  # type: ignore[arg-type]

    def dropEvent(self, event: object) -> None:  # type: ignore[override]
        if not (hasattr(event, "mimeData") and event.mimeData().hasFormat(_MIME)):  # type: ignore[union-attr]
            super().dropEvent(event)  # type: ignore[arg-type]
            return
        raw = event.mimeData().data(_MIME).data().decode()  # type: ignore[union-attr]
        paths = [Path(p) for p in raw.splitlines() if p]
        move = event.proposedAction() == Qt.DropAction.MoveAction  # type: ignore[union-attr]
        event.acceptProposedAction()  # type: ignore[union-attr]
        pane = self.parent()
        if isinstance(pane, PaneView):
            pane.files_dropped.emit(paths, move)

    def contextMenuEvent(self, event: object) -> None:  # type: ignore[override]
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
        menu.exec(event.globalPos())  # type: ignore[union-attr]


class PaneView(QWidget):
    item_activated = Signal(object)           # FileItem
    path_change_requested = Signal(object)    # Path
    mark_toggle_requested = Signal()
    back_requested = Signal()
    forward_requested = Signal()
    up_requested = Signal()
    home_requested = Signal()
    files_dropped = Signal(list, bool)        # [Path], move: bool
    context_action_requested = Signal(str)    # "copy"|"move"|"delete"|"rename"

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

        # nav bar (back/forward/up/home + path bar inline)
        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)
        for label, signal in [
            ("<", self.back_requested),
            (">", self.forward_requested),
            ("↑", self.up_requested),
            ("~", self.home_requested),
        ]:
            btn = QPushButton(label)
            btn.setFixedWidth(28)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(signal)
            nav_layout.addWidget(btn)

        self._path_bar = QLineEdit()
        self._path_bar.setPlaceholderText("Path...")
        self._path_bar.returnPressed.connect(self._on_path_entered)
        nav_layout.addWidget(self._path_bar, 1)
        layout.addWidget(nav)

        self._table = _PaneTableView(self)
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(
            COL_NAME, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSortingEnabled(True)
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
