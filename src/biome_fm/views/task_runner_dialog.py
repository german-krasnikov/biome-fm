"""TaskRunnerDialog — run Makefile/Justfile targets (F295)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from biome_fm.models.project_detector import parse_justfile_targets, parse_makefile_targets


def _collect_targets(directory: Path) -> list[tuple[str, str]]:
    """Return [(runner, target), ...] from Makefile/Justfile in directory."""
    result: list[tuple[str, str]] = []
    for filename, parser, runner in [
        ("Makefile", parse_makefile_targets, "make"),
        ("makefile", parse_makefile_targets, "make"),
        ("GNUmakefile", parse_makefile_targets, "make"),
        ("Justfile", parse_justfile_targets, "just"),
        ("justfile", parse_justfile_targets, "just"),
    ]:
        f = directory / filename
        if f.exists():
            for t in parser(f):
                result.append((runner, t))
    return result


class TaskRunnerDialog(QDialog):
    def __init__(self, directory: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Task Runner — {directory.name}")
        self.resize(600, 400)
        self._cwd = directory
        self._targets = _collect_targets(directory)
        self._proc: QProcess | None = None

        layout = QVBoxLayout(self)

        if not self._targets:
            layout.addWidget(QLabel("No Makefile or Justfile found in this directory."))
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            btns.rejected.connect(self.reject)
            layout.addWidget(btns)
            return

        self._list = QListWidget()
        for runner, target in self._targets:
            self._list.addItem(f"{runner} {target}")
        self._list.setCurrentRow(0)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("Output appears here…")

        splitter = QSplitter()
        splitter.addWidget(self._list)
        splitter.addWidget(self._output)
        splitter.setSizes([200, 400])
        layout.addWidget(splitter)

        btns = QDialogButtonBox()
        self._run_btn = btns.addButton("Run", QDialogButtonBox.ButtonRole.AcceptRole)
        btns.addButton(QDialogButtonBox.StandardButton.Close)
        self._run_btn.clicked.connect(self._run)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._list.itemDoubleClicked.connect(lambda _: self._run())

    def _run(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        runner, target = self._targets[row]
        self._output.clear()
        self._output.appendPlainText(f"$ {runner} {target}\n")
        self._run_btn.setEnabled(False)

        proc = QProcess(self)
        proc.setWorkingDirectory(str(self._cwd))
        proc.readyReadStandardOutput.connect(
            lambda: self._output.appendPlainText(
                proc.readAllStandardOutput().data().decode(errors="replace")
            )
        )
        proc.readyReadStandardError.connect(
            lambda: self._output.appendPlainText(
                proc.readAllStandardError().data().decode(errors="replace")
            )
        )
        proc.finished.connect(self._on_finished)
        self._proc = proc
        proc.start(runner, [target])

    def _on_finished(self, exit_code: int) -> None:
        self._output.appendPlainText(f"\n[exit {exit_code}]")
        self._run_btn.setEnabled(True)
        self._proc = None
