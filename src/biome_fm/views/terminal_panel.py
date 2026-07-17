"""Embedded terminal panel — QProcess shell I/O."""
from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

_OSC7_RE = re.compile(r"\x1b\]7;file://[^/]*(/.+?)\x07")

from biome_fm.qt import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProcess,
    QVBoxLayout,
    QWidget,
    Signal,
)
from biome_fm.views._panel_buttons import add_panel_buttons


def _default_shell() -> str:
    if sys.platform == "win32":
        return os.environ.get("COMSPEC", "cmd.exe")
    return os.environ.get("SHELL", "/bin/sh")


class TerminalPanel(QWidget):
    # ponytail: no VT100 escape stripping; upgrade to qtermwidget when needed
    detach_requested = Signal()
    close_requested = Signal()
    cwd_changed = Signal(Path)  # emitted when OSC 7 sequence detected

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(4, 2, 4, 2)
        hl.addWidget(QLabel("Terminal"))
        hl.addStretch()
        add_panel_buttons(hl, self.detach_requested.emit, self.close_requested.emit)
        layout.addWidget(header)

        self._out = QPlainTextEdit()
        self._out.setAccessibleName("Terminal")
        self._out.setReadOnly(True)
        self._out.setMaximumBlockCount(2000)
        layout.addWidget(self._out)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText("$ command...")
        self._inp.returnPressed.connect(self._send)
        layout.addWidget(self._inp)

        self._proc: QProcess | None = None

    def start(self, cwd: Path) -> None:
        if self._proc is not None:
            return
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(str(cwd))
        self._proc.readyReadStandardOutput.connect(self._read_out)
        self._proc.readyReadStandardError.connect(self._read_err)
        self._proc.start(_default_shell(), [])

    def set_cwd(self, path: Path) -> None:
        if self._proc and self._proc.state() == QProcess.ProcessState.Running:
            self._proc.write(f"cd {shlex.quote(str(path))}\n".encode())

    def _send(self) -> None:
        if self._proc and self._proc.state() == QProcess.ProcessState.Running:
            self._proc.write((self._inp.text() + "\n").encode())
            self._inp.clear()

    def _read_out(self) -> None:
        if self._proc:
            data = self._proc.readAllStandardOutput().data().decode("utf-8", errors="replace")
            self._out.appendPlainText(data.rstrip())
            for m in _OSC7_RE.finditer(data):
                self.cwd_changed.emit(Path(m.group(1)))

    def _read_err(self) -> None:
        if self._proc:
            data = self._proc.readAllStandardError().data().decode("utf-8", errors="replace")
            self._out.appendPlainText(data.rstrip())
