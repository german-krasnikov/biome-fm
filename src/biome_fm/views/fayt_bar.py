"""Find-As-You-Type bar with mode prefixes."""
from __future__ import annotations

from biome_fm.qt import QHBoxLayout, QLabel, QLineEdit, QWidget, Signal

_MODES = {
    "/": "navigate",
    ":": "command",
    "?": "search",
}


class FAYTBar(QWidget):
    """FAYT bar.

    Prefix  Signal emitted
    (none)  filter_changed(text)
    /       navigate_requested(text_without_prefix)
    :       command_requested(text_without_prefix)
    ?       search_requested(text_without_prefix)
    """

    filter_changed = Signal(str)
    navigate_requested = Signal(str)
    command_requested = Signal(str)
    search_requested = Signal(str)

    _SIGNAL_MAP = {
        "/": "navigate_requested",
        ":": "command_requested",
        "?": "search_requested",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        layout.addWidget(self._label)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Filter... (/ navigate  : command  ? search)")
        layout.addWidget(self._input, 1)

        self._input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str) -> None:
        if not text:
            self._label.setText("")
            self.filter_changed.emit("")
            return

        prefix = text[0]
        if prefix in self._SIGNAL_MAP:
            self._label.setText(prefix)
            signal = getattr(self, self._SIGNAL_MAP[prefix])
            signal.emit(text[1:])
        else:
            self._label.setText("")
            self.filter_changed.emit(text)
