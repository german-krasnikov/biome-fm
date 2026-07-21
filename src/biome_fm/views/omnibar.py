"""Spotlight-style popup omnibar — F411."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from biome_fm.presenters.omnibar_presenter import OmniMode, OmnibarPresenter


class OmniBar(QFrame):
    navigated = Signal(object)      # Path
    command_chosen = Signal(str)    # command name
    search_chosen = Signal(object)  # Path

    def __init__(self, presenter: OmnibarPresenter, parent=None) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._items: list = []

        self.setWindowFlags(Qt.WindowType.Popup)
        self.resize(500, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._input = QLineEdit(placeholderText="Type to search, / for path, > for commands")
        layout.addWidget(self._input)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self._debounce = QTimer(singleShot=True, interval=150)
        self._debounce.timeout.connect(self._on_query)
        self._input.textChanged.connect(self._debounce.start)
        self._list.itemActivated.connect(self._on_item_activated)

    def activate(self, root: Path) -> None:
        self._presenter.set_root(root)
        self._input.clear()
        self._list.clear()
        self._items = []
        self.show()
        self._input.setFocus()

    def _on_query(self) -> None:
        self._items = self._presenter.query_changed(self._input.text())
        self._list.clear()
        for item in self._items:
            wi = QListWidgetItem(item.label)
            if item.subtitle:
                wi.setToolTip(item.subtitle)
            self._list.addItem(wi)

    def _on_item_activated(self, wi: QListWidgetItem) -> None:
        row = self._list.row(wi)
        if not (0 <= row < len(self._items)):
            return
        item = self._items[row]
        mode = self._presenter.mode_for(self._input.text())
        if mode == OmniMode.NAVIGATE:
            self.navigated.emit(item.data)
        elif mode == OmniMode.COMMAND:
            self.command_chosen.emit(item.data)
        else:
            self.search_chosen.emit(item.data)
        self.hide()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
