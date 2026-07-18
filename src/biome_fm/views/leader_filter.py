"""LeaderFilter — global QApplication event filter for leader key sequences."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit

from biome_fm.presenters.leader_handler import LeaderHandler
from biome_fm.views.which_key_popup import WhichKeyPopup


class LeaderFilter(QObject):
    action_triggered = Signal(str)

    def __init__(
        self,
        handler: LeaderHandler,
        popup: WhichKeyPopup,
        parent: QObject | None = None,
        timer_ms: int = 300,
    ) -> None:
        super().__init__(parent)
        self._handler = handler
        self._popup = popup
        self._active = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(timer_ms)
        self._timer.timeout.connect(self._on_timeout)

    def _on_timeout(self) -> None:
        w = QApplication.focusWidget()
        self._popup.show_hints(self._handler.available(), w)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if event.type() != QEvent.Type.KeyPress:
            return False
        if isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
            return False
        key_text = event.text()  # type: ignore[attr-defined]
        if not key_text:
            return False
        result = self._handler.feed(key_text)
        if result == "pending":
            self._active = True
            self._timer.start()
            return True
        elif result == "triggered":
            self._active = False
            self._popup.hide_popup()
            self._timer.stop()
            self.action_triggered.emit("triggered")
            return True
        else:  # reset
            was_active = self._active
            self._active = False
            self._popup.hide_popup()
            self._timer.stop()
            return was_active
