"""QuickCDDialog — frecency + filesystem path completion. Alt+C (F256)."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.qt import (
    QDialog,
    QKeySequence,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QShortcut,
    Qt,
    QVBoxLayout,
    Signal,
)


class QuickCDDialog(QDialog):
    path_selected = Signal(object)  # Path

    def __init__(self, frecency_entries, cwd: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quick CD  (Alt+C)")
        self.resize(560, 320)
        layout = QVBoxLayout(self)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("Type path or filter frecency…")
        self._edit.textChanged.connect(self._on_text)
        layout.addWidget(self._edit)
        self._list = QListWidget()
        self._list.itemActivated.connect(self._on_activated)
        layout.addWidget(self._list)
        self._frecency = list(frecency_entries)
        self._cwd = cwd
        self._populate_frecency("")
        QShortcut(QKeySequence("Return"), self).activated.connect(self._on_return)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.reject)

    def _on_text(self, text: str) -> None:
        if self._is_path_like(text):
            self._populate_fs(text)
        else:
            self._populate_frecency(text)

    @staticmethod
    def _is_path_like(text: str) -> bool:
        return bool(text) and (text[0] in ("/", "~", ".") or
                               (len(text) > 1 and text[1] == ":"))

    def _populate_frecency(self, query: str) -> None:
        q = query.lower()
        entries = [e for e in self._frecency if q in str(e.path).lower()] if q else self._frecency
        self._set_items((str(e.path), e.path) for e in entries[:40])

    def _populate_fs(self, prefix: str) -> None:
        p = Path(prefix).expanduser()
        scan_dir = p if p.is_dir() else p.parent
        try:
            children = sorted(
                (e.name for e in os.scandir(scan_dir) if e.is_dir()),
                key=str.lower,
            )
        except OSError:
            children = []
        stem = "" if p.is_dir() else p.name.lower()
        filtered = [c for c in children if c.lower().startswith(stem)][:40]
        self._set_items((c, scan_dir / c) for c in filtered)

    def _set_items(self, pairs) -> None:
        self._list.clear()
        for label, path in pairs:
            item = QListWidgetItem(str(label))
            item.setData(Qt.ItemDataRole.UserRole, Path(path))
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_activated(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).is_dir():
            self.path_selected.emit(Path(path))
            self.accept()

    def _on_return(self) -> None:
        cur = self._list.currentItem()
        if cur:
            self._on_activated(cur)
        elif self._edit.text():
            p = Path(self._edit.text()).expanduser()
            if p.is_dir():
                self.path_selected.emit(p)
                self.accept()
