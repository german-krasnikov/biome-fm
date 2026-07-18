"""Sidebar panel — Volumes / Bookmarks / Recent / Tags."""
from __future__ import annotations

from pathlib import Path

from biome_fm.qt import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, Signal


class SidebarPanel(QWidget):
    path_activated = Signal(object)  # Path
    tag_activated = Signal(str)      # tag name

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(12)
        self._tree.setUniformRowHeights(True)

        for label in ("Volumes", "Bookmarks", "Recent", "Tags"):
            item = QTreeWidgetItem([label])
            self._tree.addTopLevelItem(item)
            item.setExpanded(True)

        self._tree.itemActivated.connect(self._on_activated)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

    # ── public API ────────────────────────────────────────────────────────────

    def set_volumes(self, paths: list[Path]) -> None:
        self._populate(0, {p: p.name or str(p) for p in paths})

    def set_bookmarks(self, nodes) -> None:
        from biome_fm.models.bookmark_node import display_label
        items: dict[Path, str] = {}
        self._collect_bm(nodes, items, display_label)
        self._populate(1, items)

    def set_recent(self, paths: list[Path]) -> None:
        self._populate(2, {p: p.name or str(p) for p in paths[:20]})

    def set_tags(self, tags: list[tuple[str, str]]) -> None:
        """Populate Tags section. tags = [(name, color_hex), ...]."""
        parent = self._tree.topLevelItem(3)
        parent.takeChildren()
        for name, _color in tags:
            child = QTreeWidgetItem([name])
            child.setData(0, 256, name)  # store tag name as str
            parent.addChild(child)

    # ── internals ─────────────────────────────────────────────────────────────

    def _collect_bm(self, nodes, out: dict, display_label) -> None:
        for node in nodes:
            if node.kind == "dir" and node.path is not None:
                out[node.path] = display_label(node) or node.path.name or str(node.path)
            elif node.kind == "submenu":
                self._collect_bm(node.children, out, display_label)

    def _populate(self, section: int, items: dict[Path, str]) -> None:
        parent = self._tree.topLevelItem(section)
        parent.takeChildren()
        for path, label in items.items():
            child = QTreeWidgetItem([label])
            child.setData(0, 256, path)  # Qt.UserRole = 256
            parent.addChild(child)

    def _on_activated(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, 256)
        if isinstance(data, Path):
            self.path_activated.emit(data)
        elif isinstance(data, str):
            self.tag_activated.emit(data)
