"""F237 — Quick-connect bar widget."""
from __future__ import annotations

from biome_fm.qt import QComboBox, QHBoxLayout, QPushButton, QWidget, Signal


class QuickConnectBar(QWidget):
    """QComboBox + [Connect] button. Emits connect_requested(uri)."""

    connect_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)
        self._uris: list[str] = []

        self._btn = QPushButton("Connect")
        self._btn.setFixedWidth(72)
        self._btn.clicked.connect(self._on_connect)

        layout.addWidget(self._combo, 1)
        layout.addWidget(self._btn)

    def set_profiles(self, profiles: list[tuple[str, str]]) -> None:
        """[(display_name, uri), ...] — fills combo."""
        self._combo.clear()
        self._uris = []
        for name, uri in profiles:
            self._combo.addItem(name)
            self._uris.append(uri)

    def _on_connect(self) -> None:
        idx = self._combo.currentIndex()
        if 0 <= idx < len(self._uris):
            self.connect_requested.emit(self._uris[idx])
