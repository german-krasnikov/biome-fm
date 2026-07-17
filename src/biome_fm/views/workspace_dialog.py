"""WorkspaceDialog — save/load/delete named workspace presets."""
from __future__ import annotations

from biome_fm.models.workspace_store import WorkspaceStore
from biome_fm.qt import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    Signal,
)


class WorkspaceDialog(QDialog):
    save_requested = Signal(str)    # name
    load_requested = Signal(str)    # name
    delete_requested = Signal(str)  # name

    def __init__(self, store: WorkspaceStore, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle("Workspaces")
        self.resize(300, 260)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Saved workspaces:"))
        self._list = QListWidget()
        layout.addWidget(self._list)

        btns = QHBoxLayout()
        self._btn_save = QPushButton("Save Current")
        self._btn_load = QPushButton("Load")
        self._btn_delete = QPushButton("Delete")
        for btn in (self._btn_save, self._btn_load, self._btn_delete):
            btns.addWidget(btn)
        layout.addLayout(btns)

        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)

        self._btn_save.clicked.connect(self._on_save)
        self._btn_load.clicked.connect(self._on_load)
        self._btn_delete.clicked.connect(self._on_delete)

    def _refresh(self) -> None:
        self._list.clear()
        for name in self._store.list_names():
            self._list.addItem(name)

    def _on_save(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Workspace", "Name:")
        if ok and name.strip():
            self.save_requested.emit(name.strip())
            self._refresh()

    def _on_load(self) -> None:
        item = self._list.currentItem()
        if item:
            self.load_requested.emit(item.text())

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item:
            self.delete_requested.emit(item.text())
            self._store.delete(item.text())
            self._refresh()
