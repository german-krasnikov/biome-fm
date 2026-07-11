"""AIChatPanel — passive AI chat widget."""
from __future__ import annotations

from biome_fm.qt import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    Signal,
)


class AIChatPanel(QWidget):
    """Passive chat panel. Emits message_submitted, implements AIChatViewProtocol."""

    message_submitted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Ask the AI about your files...")
        layout.addWidget(self._log)

        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Message...")
        self._send_btn = QPushButton("Send")
        row.addWidget(self._input)
        row.addWidget(self._send_btn)
        layout.addLayout(row)

        self._input.returnPressed.connect(self._on_send)
        self._send_btn.clicked.connect(self._on_send)

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.message_submitted.emit(text)

    # ── AIChatViewProtocol ───────────────────────────────────────

    def append_message(self, role: str, content: str) -> None:
        color = {"user": "#4fc3f7", "assistant": "#81c784", "error": "#ef5350"}.get(role, "#aaa")
        label = {"user": "You", "assistant": "AI", "error": "Error"}.get(role, role)
        self._log.append(f'<span style="color:{color}"><b>{label}:</b></span> {content}')

    def set_busy(self, busy: bool) -> None:
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
