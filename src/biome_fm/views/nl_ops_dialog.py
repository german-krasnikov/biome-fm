"""Natural language file operation dialog."""
from __future__ import annotations

from pathlib import Path

from biome_fm.presenters.nl_ops_presenter import NLOperation, parse_nl_operation
from biome_fm.qt import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    Signal,
)


class NLOpsDialog(QDialog):
    execute_requested = Signal(object)  # emits NLOperation

    def __init__(self, provider: object, cwd: Path, parent: QWidget | None = None,
                 prefill: str = "") -> None:
        super().__init__(parent)
        self._provider = provider
        self._cwd = cwd
        self._op: NLOperation | None = None

        self.setWindowTitle("Natural Language Operation")
        self.resize(500, 200)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Describe the file operation:"))
        self._input = QLineEdit(self)
        self._input.setPlaceholderText('e.g. "move all .txt files to docs/"')
        if prefill:
            self._input.setText(prefill)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        self._parse_btn = QPushButton("Parse", self)
        self._parse_btn.setObjectName("parse_btn")
        self._parse_btn.clicked.connect(self._on_parse)
        btn_row.addWidget(self._parse_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status = QLabel("", self)
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        action_row = QHBoxLayout()
        self._exec_btn = QPushButton("Execute", self)
        self._exec_btn.setObjectName("execute_btn")
        self._exec_btn.setEnabled(False)
        self._exec_btn.clicked.connect(self._on_execute)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        action_row.addStretch()
        action_row.addWidget(self._exec_btn)
        action_row.addWidget(cancel_btn)
        layout.addLayout(action_row)

    def _on_parse(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._status.setText("Parsing…")
        self._exec_btn.setEnabled(False)
        self._op = parse_nl_operation(text, self._cwd, self._provider)
        if self._op is None:
            self._status.setText("Could not parse — check AI provider configuration.")
        else:
            srcs = ", ".join(str(s.name) for s in self._op.sources) or "(none)"
            dst = str(self._op.destination) if self._op.destination else "(none)"
            self._status.setText(
                f"<b>{self._op.description}</b><br>"
                f"Op: {self._op.op} | Sources: {srcs} | Destination: {dst}"
            )
            self._exec_btn.setEnabled(True)

    def _on_execute(self) -> None:
        if self._op:
            self.execute_requested.emit(self._op)
            self.accept()
