"""Bookmark edit dialog — QTreeWidget with recursive node support and DnD reorder."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.qt import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QPushButton,
    Qt,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    Signal,
)

_KIND_ROLE = Qt.ItemDataRole.UserRole       # "dir" | "submenu" | "separator"
_PATH_ROLE = Qt.ItemDataRole.UserRole + 1   # str(path) for dirs
_NAME_ROLE = Qt.ItemDataRole.UserRole + 2   # custom name for dirs (avoids text parsing)


class _BookmarkTree(QTreeWidget):
    tree_changed = Signal()

    def dropEvent(self, event) -> None:
        if event.source() is self:
            super().dropEvent(event)
            self.tree_changed.emit()
        else:
            event.ignore()


class BookmarkDialog(QDialog):
    _DND_MIME = "application/x-biome-fm-paths"
    bookmark_chosen = Signal(Path)

    def __init__(self, store, bus=None, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("Edit Bookmarks")
        self.setAcceptDrops(True)
        self.resize(440, 400)
        self._store = store
        self._bus = bus
        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        self._tree = _BookmarkTree()
        self._tree.setHeaderHidden(True)
        self._tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self._tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.tree_changed.connect(self._sync_tree)
        layout.addWidget(self._tree, 1)

        btn_layout = QVBoxLayout()
        self._btn_add = QPushButton("Add Dir")
        self._btn_add_submenu = QPushButton("Add Submenu")
        self._btn_add_sep = QPushButton("Add Separator")
        self._btn_rename = QPushButton("Rename")
        self._btn_remove = QPushButton("Delete")
        self._btn_up = QPushButton("Up")
        self._btn_down = QPushButton("Down")
        self._btn_close = QPushButton("Close")

        for btn in (self._btn_add, self._btn_add_submenu, self._btn_add_sep,
                    self._btn_rename, self._btn_remove, self._btn_up, self._btn_down):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_close)
        layout.addLayout(btn_layout)

        self._btn_add.clicked.connect(self._on_add)
        self._btn_add_submenu.clicked.connect(self._on_add_submenu)
        self._btn_add_sep.clicked.connect(self._on_add_sep)
        self._btn_rename.clicked.connect(self._on_rename)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(lambda: self._move(-1))
        self._btn_down.clicked.connect(lambda: self._move(1))
        self._btn_close.clicked.connect(self.close)

    def _refresh(self) -> None:
        expanded = self._expanded_names()
        sel_path = self._selected_path()
        self._tree.clear()
        self._populate(self._tree.invisibleRootItem(), self._store.tree())
        self._restore_expanded(expanded)
        if sel_path:
            self._select_by_path(sel_path)

    def _populate(self, parent: QTreeWidgetItem, nodes: list[BookmarkNode]) -> None:
        for node in nodes:
            item = QTreeWidgetItem()
            if node.kind == "dir":
                label = node.name or (node.path.name if node.path else "")
                text = (f"{label}  —  {node.path}"
                        if label and label != str(node.path) else str(node.path))
                item.setText(0, text)
                item.setData(0, _KIND_ROLE, "dir")
                item.setData(0, _PATH_ROLE, str(node.path))
                item.setData(0, _NAME_ROLE, node.name or "")
            elif node.kind == "submenu":
                item.setText(0, node.name)
                item.setData(0, _KIND_ROLE, "submenu")
            else:  # separator
                item.setText(0, "──────────")
                item.setData(0, _KIND_ROLE, "separator")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            parent.addChild(item)
            if node.kind == "submenu":
                self._populate(item, node.children)

    def _sync_tree(self) -> None:
        def _read(parent: QTreeWidgetItem) -> list[BookmarkNode]:
            nodes = []
            for i in range(parent.childCount()):
                item = parent.child(i)
                kind = item.data(0, _KIND_ROLE)
                if kind == "dir":
                    name = item.data(0, _NAME_ROLE) or ""
                    nodes.append(BookmarkNode("dir", Path(item.data(0, _PATH_ROLE)), name))
                elif kind == "submenu":
                    nodes.append(BookmarkNode("submenu", name=item.text(0),
                                              children=_read(item)))
                else:
                    nodes.append(BookmarkNode("separator"))
            return nodes
        self._store.set_tree(_read(self._tree.invisibleRootItem()))
        self._publish()

    def _expanded_names(self) -> set[str]:
        root = self._tree.invisibleRootItem()
        return {root.child(i).text(0) for i in range(root.childCount())
                if root.child(i).isExpanded()}

    def _restore_expanded(self, names: set[str]) -> None:
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) in names:
                item.setExpanded(True)

    def _selected_path(self) -> Path | None:
        item = self._tree.currentItem()
        if item and item.data(0, _KIND_ROLE) == "dir":
            return Path(item.data(0, _PATH_ROLE))
        return None

    def _select_by_path(self, path: Path) -> None:
        def _search(parent: QTreeWidgetItem, target: str) -> bool:
            for i in range(parent.childCount()):
                item = parent.child(i)
                if item.data(0, _PATH_ROLE) == target:
                    self._tree.setCurrentItem(item)
                    return True
                if _search(item, target):
                    return True
            return False
        _search(self._tree.invisibleRootItem(), str(path))

    def _current_parent(self) -> QTreeWidgetItem:
        """Return selected submenu item, or the invisible root."""
        current = self._tree.currentItem()
        if current and current.data(0, _KIND_ROLE) == "submenu":
            return current
        return self._tree.invisibleRootItem()

    def _on_add(self) -> None:
        text, ok = QInputDialog.getText(self, "Add Bookmark", "Path:")
        if not ok or not text.strip():
            return
        p = Path(text.strip()).expanduser()
        if p in self._store:
            return
        parent_item = self._current_parent()
        item = QTreeWidgetItem()
        label = p.name or str(p)
        item.setText(0, f"{label}  —  {p}")
        item.setData(0, _KIND_ROLE, "dir")
        item.setData(0, _PATH_ROLE, str(p))
        item.setData(0, _NAME_ROLE, "")
        parent_item.addChild(item)
        if parent_item is not self._tree.invisibleRootItem():
            parent_item.setExpanded(True)
        self._sync_tree()
        self._refresh()

    def _on_add_submenu(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Submenu", "Name:")
        if not ok or not name.strip():
            return
        item = QTreeWidgetItem()
        item.setText(0, name.strip())
        item.setData(0, _KIND_ROLE, "submenu")
        self._current_parent().addChild(item)
        self._sync_tree()
        self._refresh()

    def _on_add_sep(self) -> None:
        item = QTreeWidgetItem()
        item.setText(0, "──────────")
        item.setData(0, _KIND_ROLE, "separator")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        current = self._tree.currentItem()
        if current:
            parent = current.parent() or self._tree.invisibleRootItem()
            idx = parent.indexOfChild(current)
            parent.insertChild(idx + 1, item)
        else:
            self._tree.invisibleRootItem().addChild(item)
        self._sync_tree()
        self._refresh()

    def _on_remove(self) -> None:
        item = self._tree.currentItem()
        if not item:
            return
        parent = item.parent() or self._tree.invisibleRootItem()
        parent.removeChild(item)
        self._sync_tree()
        self._refresh()

    def _on_rename(self) -> None:
        item = self._tree.currentItem()
        if not item or item.data(0, _KIND_ROLE) == "separator":
            return
        is_dir = item.data(0, _KIND_ROLE) == "dir"
        current_text = item.data(0, _NAME_ROLE) or "" if is_dir else item.text(0)
        name, ok = QInputDialog.getText(self, "Rename", "Name:", text=current_text)
        if not ok:
            return
        name = name.strip()
        if is_dir:
            path_str = item.data(0, _PATH_ROLE)
            item.setText(0, f"{name}  —  {path_str}" if name else path_str)
            item.setData(0, _NAME_ROLE, name)
        else:
            item.setText(0, name)
        self._sync_tree()
        self._refresh()

    def _move(self, delta: int) -> None:
        item = self._tree.currentItem()
        if not item:
            return
        parent = item.parent() or self._tree.invisibleRootItem()
        idx = parent.indexOfChild(item)
        new_idx = idx + delta
        if 0 <= new_idx < parent.childCount():
            parent.takeChild(idx)
            parent.insertChild(new_idx, item)
            self._tree.setCurrentItem(item)
        self._sync_tree()
        self._refresh()

    def _on_double_click(self, item, _col=None) -> None:
        if item and item.data(0, _KIND_ROLE) == "dir":
            self.bookmark_chosen.emit(Path(item.data(0, _PATH_ROLE)))

    def _publish(self) -> None:
        if self._bus:
            from biome_fm.event_bus import BookmarkChanged
            self._bus.publish(BookmarkChanged())

    def _handle_drop(self, mime) -> None:
        if mime.hasFormat(self._DND_MIME):
            raw = mime.data(self._DND_MIME).data().decode()
            paths = [Path(p) for p in raw.splitlines() if p.strip()]
        elif mime.hasUrls():
            paths = [Path(u.toLocalFile()) for u in mime.urls() if u.isLocalFile()]
        else:
            return
        if not paths:
            return
        before = len(self._store.all())
        for p in paths:
            self._store.add(p)
        if len(self._store.all()) > before:
            self._publish()
        self._refresh()

    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md.hasFormat(self._DND_MIME) or any(u.isLocalFile() for u in md.urls()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        self._handle_drop(event.mimeData())
        event.acceptProposedAction()
