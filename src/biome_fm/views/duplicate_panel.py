"""Duplicate file finder dialog."""
from __future__ import annotations

import queue
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog, QLabel, QProgressBar, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)

from biome_fm.presenters.duplicate_presenter import DupGroup, find_duplicates


class DuplicateFinderDialog(QDialog):
    delete_requested = Signal(list)  # list[Path]

    def __init__(self, root: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Duplicates in {root.name}")
        self.resize(600, 400)

        self._status = QLabel("Scanning...")
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["File", "Size"])
        self._tree.setUniformRowHeights(True)
        self._del_btn = QPushButton("Delete Duplicates (keep first)")
        self._del_btn.setEnabled(False)
        self._del_btn.clicked.connect(self._on_delete)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(self._progress)
        layout.addWidget(self._tree)
        layout.addWidget(self._del_btn)

        self._groups: list[DupGroup] = []
        self._cancel: list[bool] = [False]
        self._queue: queue.SimpleQueue = queue.SimpleQueue()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._drain)
        self._timer.start(100)

        self._thread = threading.Thread(target=self._scan, args=(root,), daemon=True)
        self._thread.start()

    def _scan(self, root: Path) -> None:
        self._queue.put(find_duplicates(root, self._cancel))

    def _drain(self) -> None:
        try:
            groups = self._queue.get_nowait()
        except queue.Empty:
            return
        self._timer.stop()
        self._groups = groups
        self._progress.setRange(0, 1)
        self._progress.setValue(1)
        self._tree.clear()
        total = 0
        for g in groups:
            root_item = QTreeWidgetItem(
                [f"{len(g.paths)} duplicates ({_fmt(g.size)})", ""]
            )
            for p in g.paths:
                child = QTreeWidgetItem([str(p), _fmt(g.size)])
                child.setData(0, Qt.ItemDataRole.UserRole, p)
                root_item.addChild(child)
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)
            total += len(g.paths) - 1
        self._status.setText(f"{len(groups)} groups, {total} deletable files")
        self._del_btn.setEnabled(bool(groups))

    def _on_delete(self) -> None:
        to_delete = [p for g in self._groups for p in g.paths[1:]]
        self.delete_requested.emit(to_delete)
        self.accept()

    def closeEvent(self, event) -> None:
        self._cancel[0] = True
        self._timer.stop()
        if self._thread.is_alive():
            self._thread.join(timeout=2)
        super().closeEvent(event)


def _fmt(n: int) -> str:
    s = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024:
            return f"{s:.1f} {unit}"
        s /= 1024
    return f"{s:.1f} TB"
