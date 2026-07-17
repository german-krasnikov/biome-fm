"""AIChatPanel — AI chat with bubbles, DnD, model selector, streaming."""
from __future__ import annotations

from pathlib import Path

from biome_fm.qt import (
    QComboBox,
    QHBoxLayout,
    QKeyEvent,
    QPushButton,
    Qt,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views._chat_log import ChatLog
from biome_fm.views._context_bar import ContextBar

_INTERNAL_MIME = "application/x-biome-fm-paths"


class _ChatInput(QTextEdit):
    """Multi-line input: Enter=send, Shift+Enter=newline."""

    send_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Message... (Enter to send, Shift+Enter for newline)")
        self.setMaximumHeight(100)
        self.setAcceptDrops(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.send_requested.emit()
            return
        super().keyPressEvent(event)


class AIChatPanel(QWidget):
    """Full AI chat panel with bubbles, DnD context, model selector."""

    message_submitted = Signal(str)
    model_changed = Signal(str)
    provider_changed = Signal(str)
    cancel_requested = Signal()
    attachment_dropped = Signal(object)  # Path
    detach_requested = Signal()
    close_requested = Signal()
    file_link_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header: provider + model combos
        header = QHBoxLayout()
        header.setSpacing(4)
        self._provider_combo = QComboBox()
        self._provider_combo.setMinimumWidth(80)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(100)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        header.addWidget(self._provider_combo)
        header.addWidget(self._model_combo)
        header.addStretch()
        from biome_fm.views._panel_buttons import add_panel_buttons
        add_panel_buttons(header, self.detach_requested, self.close_requested)
        layout.addLayout(header)

        # Chat log (bubbles)
        self._log = ChatLog()
        self._log.setPlaceholderText("Ask the AI about your files...")
        self._log.path_link_clicked.connect(self.file_link_clicked)
        layout.addWidget(self._log, 1)

        # Context bar (attachment chips)
        self._context_bar = ContextBar()
        layout.addWidget(self._context_bar)

        # Input area
        input_row = QHBoxLayout()
        input_row.setSpacing(4)
        self._input = _ChatInput()
        self._input.send_requested.connect(self._on_send)
        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(60)
        self._send_btn.clicked.connect(self._on_send)
        self._cancel_btn = QPushButton("x")
        self._cancel_btn.setFixedWidth(28)
        self._cancel_btn.setToolTip("Cancel (Esc)")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        self._cancel_btn.hide()
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._send_btn)
        input_row.addWidget(self._cancel_btn)
        layout.addLayout(input_row)

    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if text:
            self._input.clear()
            self.message_submitted.emit(text)

    def _on_provider_changed(self, name: str) -> None:
        if name:
            self.provider_changed.emit(name)

    def _on_model_changed(self, name: str) -> None:
        if name:
            self.model_changed.emit(name)

    # ── AIChatViewProtocol ────────────────────────────────────────

    def append_message(self, role: str, content: str) -> None:
        self._log.append_bubble(role, content)

    def set_busy(self, busy: bool) -> None:
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._cancel_btn.setVisible(busy)
        if busy:
            self._log.show_thinking()
        else:
            self._log.hide_thinking()

    def append_tool_event(self, description: str) -> None:
        self._log.append_tool_event(description)

    def append_token(self, token: str) -> None:
        self._log.stream_token(token)

    def finalize_stream(self) -> None:
        self._log.stream_end()

    def discard_stream(self) -> None:
        self._log.stream_discard()

    def add_attachment_chip(self, name: str) -> None:
        self._context_bar.add_chip(name)

    def clear_attachment_chips(self) -> None:
        self._context_bar.clear_chips()

    def set_provider_list(
        self,
        providers: list[str],
        active: str,
        models: list[str],
        active_model: str,
    ) -> None:
        self._provider_combo.blockSignals(True)
        self._model_combo.blockSignals(True)
        self._provider_combo.clear()
        self._provider_combo.addItems(providers)
        if active in providers:
            self._provider_combo.setCurrentText(active)
        self._model_combo.clear()
        self._model_combo.addItems(models)
        if active_model in models:
            self._model_combo.setCurrentText(active_model)
        self._provider_combo.blockSignals(False)
        self._model_combo.blockSignals(False)

    # ── Drag & Drop ───────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasFormat(_INTERNAL_MIME) or mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for p in self._paths_from_mime(event.mimeData()):
            self.attachment_dropped.emit(p)
        event.acceptProposedAction()

    def _paths_from_mime(self, mime) -> list[Path]:
        if mime.hasFormat(_INTERNAL_MIME):
            raw = bytes(mime.data(_INTERNAL_MIME)).decode("utf-8")
            return [p for s in raw.splitlines()
                    if s and (p := Path(s).resolve()).exists()]
        if mime.hasUrls():
            return [p for u in mime.urls()
                    if u.isLocalFile() and (p := Path(u.toLocalFile()).resolve()).exists()]
        return []

    # ── Keyboard ──────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_requested.emit()
            return
        super().keyPressEvent(event)
