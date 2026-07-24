"""AI Context Actions dialog — shows AI-suggested actions for selected files."""
from __future__ import annotations

import queue as _queue
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class AIContextDialog(QDialog):
    """Show AI-suggested action labels for a list of files."""

    def __init__(self, items: list[str], provider: object, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Actions")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Suggested actions for: {', '.join(items)}"))

        self._loading = QLabel("Loading…")
        layout.addWidget(self._loading)

        self._list = QListWidget()
        self._list.setVisible(False)
        layout.addWidget(self._list)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_selected)
        layout.addWidget(copy_btn)

        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(self.reject)
        layout.addWidget(btn)

        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai-ctx")
        self._result_q: _queue.SimpleQueue[str] = _queue.SimpleQueue()
        self._poll = QTimer(self)
        self._poll.setInterval(50)
        self._poll.timeout.connect(self._drain)

        if getattr(provider, "available", False):
            prompt = (
                f"For these files: {', '.join(items)}. "
                "Suggest 3-5 brief action labels (one per line)."
            )
            self._pool.submit(self._run_chat, provider, prompt)
            self._poll.start()
        else:
            self._loading.setText("AI not configured")

    def _run_chat(self, provider: object, prompt: str) -> None:
        """Background thread — no Qt."""
        try:
            text = provider.chat([{"role": "user", "content": prompt}])
        except Exception:
            text = ""
        self._result_q.put(text)

    def _drain(self) -> None:
        try:
            text = self._result_q.get_nowait()
        except _queue.Empty:
            return
        self._poll.stop()
        self._loading.setVisible(False)
        for line in text.splitlines():
            line = line.strip().lstrip("0123456789.-) ")
            if line:
                self._list.addItem(line)
        self._list.setVisible(True)

    def _copy_selected(self) -> None:
        item = self._list.currentItem()
        if item:
            QApplication.clipboard().setText(item.text())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._poll.stop()
        self._pool.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
