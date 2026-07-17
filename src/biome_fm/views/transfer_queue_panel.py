"""TransferQueuePanel — live view of active/completed file transfers."""
from __future__ import annotations

from collections.abc import Callable

from biome_fm.qt import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _TransferRow(QWidget):
    def __init__(self, task_id: int, description: str, cancel_cb: Callable[[int], None]) -> None:
        super().__init__()
        self._task_id = task_id
        self._cancel = cancel_cb

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(2)

        self._desc = QLabel(description)
        self._desc.setStyleSheet("font-weight: bold;")
        root.addWidget(self._desc)

        self._file_label = QLabel()
        self._file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        root.addWidget(self._file_label)

        bottom = QHBoxLayout()
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        bottom.addWidget(self._bar)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMaximumWidth(70)
        self._cancel_btn.clicked.connect(lambda: self._cancel(self._task_id))
        bottom.addWidget(self._cancel_btn)

        self._status = QLabel()
        self._status.hide()
        bottom.addWidget(self._status)

        root.addLayout(bottom)

    def update_progress(self, files_done: int, files_total: int,
                        bytes_done: int, bytes_total: int, current_file: str) -> None:
        self._bar.setRange(0, max(bytes_total, 1))
        self._bar.setValue(bytes_done)
        if files_total:
            self._file_label.setText(f"{current_file}  ({files_done}/{files_total})")
        else:
            self._file_label.setText(current_file)

    def _finalize(self, status: str) -> None:
        self._bar.hide()
        self._cancel_btn.hide()
        self._status.setText(status)
        self._status.show()

    def mark_done(self) -> None:
        self._finalize("✓ Done")

    def mark_error(self, msg: str) -> None:
        self._finalize(f"✗ {msg}")

    def mark_cancelled(self) -> None:
        self._finalize("⊘ Cancelled")


class TransferQueuePanel(QWidget):
    """Shows active + recent file transfers. Driven by method calls on the main thread."""

    def __init__(self, cancel_cb: Callable[[int], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cancel_cb = cancel_cb
        self._rows: dict[int, _TransferRow] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Transfers")
        header.setStyleSheet("font-weight: bold; padding: 4px;")
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        outer.addWidget(scroll)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._layout.addStretch(1)
        scroll.setWidget(self._container)

    def on_op_started(self, task_id: int, description: str) -> None:
        row = _TransferRow(task_id, description, self._cancel_cb)
        self._rows[task_id] = row
        # Insert before the trailing stretch
        idx = self._layout.count() - 1
        self._layout.insertWidget(idx, row)

    def on_op_progress(self, task_id: int, files_done: int, files_total: int,
                       bytes_done: int, bytes_total: int, current_file: str) -> None:
        row = self._rows.get(task_id)
        if row:
            row.update_progress(files_done, files_total, bytes_done, bytes_total, current_file)

    def on_op_done(self, task_id: int) -> None:
        row = self._rows.get(task_id)
        if row:
            row.mark_done()

    def on_op_error(self, task_id: int, error: str) -> None:
        row = self._rows.get(task_id)
        if row:
            row.mark_error(error)

    def on_op_cancelled(self, task_id: int) -> None:
        row = self._rows.get(task_id)
        if row:
            row.mark_cancelled()
