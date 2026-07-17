"""OpenWithDialog — choose app or enter custom command to open a file."""
from __future__ import annotations

from biome_fm.models.app_chooser import discover_apps
from biome_fm.qt import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    Qt,
    QVBoxLayout,
    Signal,
)


class OpenWithDialog(QDialog):
    app_selected = Signal(str)  # emits command string

    def __init__(self, file_name: str = "", parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle(f"Open With — {file_name}" if file_name else "Open With")
        self.resize(400, 320)
        self._apps = discover_apps()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Available applications:"))
        self._list = QListWidget()
        for app in self._apps:
            self._list.addItem(app["name"])
        self._list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        layout.addWidget(QLabel("Or enter custom command ({f} = file path):"))
        self._custom = QLineEdit()
        self._custom.setPlaceholderText("e.g.  vim {f}")
        layout.addWidget(self._custom)

        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self._on_ok)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _on_ok(self) -> None:
        custom = self._custom.text().strip()
        if custom:
            self.app_selected.emit(custom)
            self.accept()
            return
        row = self._list.currentRow()
        if 0 <= row < len(self._apps):
            self.app_selected.emit(self._apps[row]["command"])
            self.accept()

    def _on_double_click(self, _item) -> None:
        self._on_ok()
