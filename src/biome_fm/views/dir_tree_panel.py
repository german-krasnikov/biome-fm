"""DirTreePanel — directory tree navigation side panel."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex
from PySide6.QtWidgets import QFileSystemModel

from biome_fm.qt import QTreeView, QVBoxLayout, QWidget, Signal


class DirTreePanel(QWidget):
    path_selected = Signal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self._model.setRootPath("")

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setUniformRowHeights(True)
        self._tree.setHeaderHidden(True)
        # Hide size/type/modified columns — dirs only need name
        for col in range(1, 4):
            self._tree.hideColumn(col)
        self._tree.activated.connect(self._on_index_activated)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)

    def set_root(self, path: Path) -> None:
        idx = self._model.index(str(path))
        self._tree.setRootIndex(idx)
        self._tree.expand(idx)

    def _on_index_activated(self, index: QModelIndex) -> None:
        self._on_activated(Path(self._model.filePath(index)))

    def _on_activated(self, path: Path) -> None:
        self.path_selected.emit(path)
