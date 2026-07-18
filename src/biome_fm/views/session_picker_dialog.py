"""SessionPickerDialog — browse, save, delete named sessions (F267)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from biome_fm.models.session_store import SessionStore


class SessionPickerDialog(QDialog):
    """Lists named sessions; returns selected name via `selected_name` attr."""

    def __init__(self, store: SessionStore, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Named Sessions")
        self.setMinimumWidth(320)
        self._store = store
        self.selected_name: str | None = None

        self._list = QListWidget()
        self._refresh()

        btn_load = QPushButton("Load")
        btn_new = QPushButton("Save As…")
        btn_del = QPushButton("Delete")
        btn_close = QPushButton("Close")

        btn_load.clicked.connect(self._load)
        btn_new.clicked.connect(self._new)
        btn_del.clicked.connect(self._delete)
        btn_close.clicked.connect(self.reject)

        btns = QHBoxLayout()
        for b in (btn_load, btn_new, btn_del, btn_close):
            btns.addWidget(b)

        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        layout.addLayout(btns)

    def _refresh(self) -> None:
        current = self._list.currentItem()
        cur_text = current.text() if current else None
        self._list.clear()
        for name in self._store.list_sessions():
            self._list.addItem(name)
        if cur_text:
            found = self._list.findItems(cur_text, Qt.MatchFlag.MatchExactly)
            if found:
                self._list.setCurrentItem(found[0])

    def _current_name(self) -> str | None:
        item = self._list.currentItem()
        return item.text() if item else None

    def _load(self) -> None:
        name = self._current_name()
        if name:
            self.selected_name = name
            self.accept()

    def _new(self) -> None:
        """Emit signal for caller to supply state — store returned via `save_name`."""
        name, ok = QInputDialog.getText(self, "Save Session", "Session name:")
        if ok and name.strip():
            self.save_name = name.strip()
            self.accept()

    def _delete(self) -> None:
        name = self._current_name()
        if not name:
            return
        answer = QMessageBox.question(self, "Delete Session", f"Delete '{name}'?")
        if answer == QMessageBox.StandardButton.Yes:
            self._store.delete_session(name)
            self._refresh()
