"""MenuBuilderDialog — GUI editor for user-defined context menu actions."""
from __future__ import annotations

from biome_fm.models.user_actions import UserAction, UserActionsStore
from biome_fm.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    Qt,
    QVBoxLayout,
)


class MenuBuilderDialog(QDialog):
    """List + Add/Edit/Remove UI for UserActionsStore."""

    def __init__(self, store: UserActionsStore, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("Custom Context Menu Actions")
        self.resize(500, 380)
        self._store = store
        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_select)
        layout.addWidget(self._list, 1)

        right = QVBoxLayout()

        form = QFormLayout()
        self._lbl = QLineEdit()
        self._cmd = QLineEdit()
        self._ext = QLineEdit()
        self._ext.setPlaceholderText(".py, .txt  (empty = all)")
        form.addRow(QLabel("Label:"), self._lbl)
        form.addRow(QLabel("Command:"), self._cmd)
        form.addRow(QLabel("Extensions:"), self._ext)
        right.addLayout(form)

        self._btn_add = QPushButton("Add")
        self._btn_upd = QPushButton("Update")
        self._btn_del = QPushButton("Remove")
        self._btn_add.clicked.connect(self._on_add)
        self._btn_upd.clicked.connect(self._on_update)
        self._btn_del.clicked.connect(self._on_remove)
        for b in (self._btn_add, self._btn_upd, self._btn_del):
            right.addWidget(b)

        right.addStretch()
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.close)
        right.addWidget(bbox)

        layout.addLayout(right)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._list.clear()
        for a in self._store.all():
            ext = ", ".join(a.extensions) if a.extensions else "(all)"
            self._list.addItem(f"{a.label}  [{ext}]  →  {a.command}")

    def _current_action(self) -> UserAction | None:
        idx = self._list.currentRow()
        if idx < 0:
            return None
        return self._store.all()[idx]

    def _read_fields(self) -> UserAction:
        exts = [e.strip() for e in self._ext.text().split(",") if e.strip()]
        return UserAction(
            label=self._lbl.text().strip(),
            command=self._cmd.text().strip(),
            extensions=exts,
        )

    # ── slots ─────────────────────────────────────────────────────────────────

    def _on_select(self, row: int) -> None:
        actions = self._store.all()
        if 0 <= row < len(actions):
            a = actions[row]
            self._lbl.setText(a.label)
            self._cmd.setText(a.command)
            self._ext.setText(", ".join(a.extensions))

    def _on_add(self) -> None:
        self._store.add(self._read_fields())
        self._store.save()
        self._refresh()

    def _on_update(self) -> None:
        idx = self._list.currentRow()
        if 0 <= idx < len(self._store.all()):
            self._store.update(idx, self._read_fields())
            self._store.save()
            self._refresh()

    def _on_remove(self) -> None:
        idx = self._list.currentRow()
        if idx >= 0:
            self._store.remove(idx)
            self._store.save()
            self._refresh()
