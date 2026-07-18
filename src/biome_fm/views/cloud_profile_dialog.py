"""F301 — Cloud Storage Profile Manager dialog. Passive view."""
from __future__ import annotations

from biome_fm.models.cloud_profile_store import CloudProfile, CloudProfileStore
from biome_fm.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_SCHEMES = ["s3", "sftp", "ssh", "ftp", "ftps", "webdav", "rclone"]


class CloudProfileDialog(QDialog):
    """CRUD dialog: list on the left, edit form on the right."""

    def __init__(self, store: CloudProfileStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle("Cloud Profiles")
        self.resize(600, 400)
        self._build_ui()
        self._refresh_list()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        # Left: list + buttons
        left = QVBoxLayout()
        self._list = QListWidget()
        self._list.currentTextChanged.connect(self._on_select)
        left.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._btn_new = QPushButton("New")
        self._btn_delete = QPushButton("Delete")
        self._btn_new.clicked.connect(self._on_new)
        self._btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(self._btn_new)
        btn_row.addWidget(self._btn_delete)
        left.addLayout(btn_row)
        root.addLayout(left, 1)

        # Right: form
        right = QVBoxLayout()
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._scheme_combo = QComboBox()
        for s in _SCHEMES:
            self._scheme_combo.addItem(s)
        self._host_edit = QLineEdit()
        self._port_edit = QLineEdit()
        self._port_edit.setPlaceholderText("default")
        self._user_edit = QLineEdit()
        self._bucket_edit = QLineEdit()

        form.addRow("Name:", self._name_edit)
        form.addRow("Scheme:", self._scheme_combo)
        form.addRow("Host:", self._host_edit)
        form.addRow("Port:", self._port_edit)
        form.addRow("User:", self._user_edit)
        form.addRow("Bucket:", self._bucket_edit)
        right.addLayout(form)

        btn_box = QDialogButtonBox()
        self._btn_save = btn_box.addButton("Save", QDialogButtonBox.ButtonRole.ApplyRole)
        self._btn_test = btn_box.addButton("Test Connection", QDialogButtonBox.ButtonRole.ActionRole)
        self._btn_close = btn_box.addButton(QDialogButtonBox.StandardButton.Close)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_close.clicked.connect(self.close)
        right.addWidget(btn_box)
        root.addLayout(right, 2)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        self._list.clear()
        for p in self._store.list_all():
            self._list.addItem(p.name)

    def _on_select(self, name: str) -> None:
        p = self._store.get(name)
        if p is None:
            return
        self._name_edit.setText(p.name)
        idx = self._scheme_combo.findText(p.scheme)
        if idx >= 0:
            self._scheme_combo.setCurrentIndex(idx)
        self._host_edit.setText(p.host)
        self._port_edit.setText(str(p.port) if p.port else "")
        self._user_edit.setText(p.user)
        self._bucket_edit.setText(p.bucket)

    def _on_new(self) -> None:
        self._name_edit.clear()
        self._host_edit.clear()
        self._port_edit.clear()
        self._user_edit.clear()
        self._bucket_edit.clear()
        self._scheme_combo.setCurrentIndex(0)

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            return
        port_text = self._port_edit.text().strip()
        port = int(port_text) if port_text.isdigit() else None
        p = CloudProfile(
            name=name,
            scheme=self._scheme_combo.currentText(),
            host=self._host_edit.text().strip(),
            port=port,
            user=self._user_edit.text().strip(),
            bucket=self._bucket_edit.text().strip(),
        )
        self._store.add(p)
        self._store.save()
        self._refresh_list()

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        self._store.delete(item.text())
        self._store.save()
        self._refresh_list()
