"""Modeless progress dialog for async file operations."""
from __future__ import annotations

from collections.abc import Callable

from biome_fm.qt import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout


class ProgressDialog(QDialog):
    def __init__(self, task_id: int, description: str, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.task_id = task_id
        self.setWindowTitle(description)
        self.setModal(False)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        self._file_label = QLabel("Preparing...")
        self._bytes_bar = QProgressBar()
        self._overall_label = QLabel("")
        self._files_bar = QProgressBar()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        widgets = (self._file_label, self._bytes_bar, self._overall_label,
                   self._files_bar, self._cancel_btn)
        for w in widgets:
            layout.addWidget(w)
        self._cancel_cb: Callable[[], None] | None = None

    def set_cancel_callback(self, cb: Callable[[], None]) -> None:
        self._cancel_cb = cb

    def update_progress(self, event: object) -> None:
        self._file_label.setText(event.current_file)  # type: ignore[attr-defined]
        if event.bytes_total > 0:  # type: ignore[attr-defined]
            self._bytes_bar.setMaximum(event.bytes_total)  # type: ignore[attr-defined]
            self._bytes_bar.setValue(event.bytes_done)  # type: ignore[attr-defined]
        self._overall_label.setText(f"{event.files_done} / {event.files_total}")  # type: ignore[attr-defined]
        self._files_bar.setMaximum(max(event.files_total, 1))  # type: ignore[attr-defined]
        self._files_bar.setValue(event.files_done)  # type: ignore[attr-defined]

    def mark_done(self) -> None:
        self.accept()

    def mark_error(self, error: object) -> None:
        self._file_label.setText(f"Error: {error}")
        self._cancel_btn.setText("Close")
        self._cancel_cb = None

    def mark_cancelled(self) -> None:
        self.reject()

    def _on_cancel(self) -> None:
        if self._cancel_cb:
            self._cancel_cb()
        else:
            self.reject()
