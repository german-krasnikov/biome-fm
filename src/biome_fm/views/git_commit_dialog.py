"""Git commit dialog with optional AI-assisted message suggestion."""
from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QPlainTextEdit,
    QPushButton, QVBoxLayout,
)

from biome_fm.git.commit_ops import commit, staged_diff, staged_files
from biome_fm.presenters.ai_diff_summary import diff_summary_prompt


class _AISuggestWorker(QRunnable):
    class Signals(QObject):
        done = Signal(str)

    def __init__(self, diff: str, ai_call) -> None:
        super().__init__()
        self._diff = diff
        self._ai_call = ai_call
        self.signals = _AISuggestWorker.Signals()

    def run(self) -> None:
        try:
            if inspect.iscoroutinefunction(self._ai_call):
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(self._ai_call(diff_summary_prompt(self._diff)))
                loop.close()
            else:
                result = self._ai_call(diff_summary_prompt(self._diff))
        except Exception:
            result = ""
        self.signals.done.emit(result)


class GitCommitDialog(QDialog):
    def __init__(self, repo: Path, ai_call=None, parent=None) -> None:
        super().__init__(parent)
        self._repo = repo
        self._ai_call = ai_call
        self.setWindowTitle("Commit")
        self.resize(500, 300)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        files = staged_files(self._repo)
        layout.addWidget(QLabel(f"{len(files)} file(s) staged"))

        self._msg = QPlainTextEdit()
        self._msg.setPlaceholderText("Commit message…")
        layout.addWidget(self._msg)

        if self._ai_call is not None:
            btn = QPushButton("AI Suggest")
            btn.clicked.connect(self._ai_suggest)
            layout.addWidget(btn)

        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self._do_commit)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _ai_suggest(self) -> None:
        diff = staged_diff(self._repo)
        if not diff:
            return
        worker = _AISuggestWorker(diff, self._ai_call)
        worker.signals.done.connect(self._msg.setPlainText)
        QThreadPool.globalInstance().start(worker)

    def _do_commit(self) -> None:
        msg = self._msg.toPlainText().strip()
        if not msg:
            return
        try:
            commit(self._repo, msg)
            self.accept()
        except (ValueError, RuntimeError) as e:
            self._msg.setPlainText(f"Error: {e}")
