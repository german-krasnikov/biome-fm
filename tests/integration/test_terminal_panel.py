"""Integration tests for TerminalPanel widget."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_terminal_instantiates(qtbot):
    from biome_fm.views.terminal_panel import TerminalPanel
    tp = TerminalPanel()
    qtbot.addWidget(tp)
    assert tp._out is not None
    assert tp._inp is not None


def test_terminal_has_signals(qtbot):
    from biome_fm.views.terminal_panel import TerminalPanel
    tp = TerminalPanel()
    qtbot.addWidget(tp)
    assert hasattr(tp, "detach_requested")
    assert hasattr(tp, "close_requested")


# F255 — Subshell CWD Sync: verify cwd_changed fires on OSC 7 sequence
def test_cwd_changed_fires_on_osc7(qtbot):
    from biome_fm.views.terminal_panel import TerminalPanel
    tp = TerminalPanel()
    qtbot.addWidget(tp)
    received: list[Path] = []
    tp.cwd_changed.connect(received.append)

    # Inject a mock _proc that returns OSC 7 data
    mock_proc = MagicMock()
    osc7 = b"\x1b]7;file://hostname/tmp/testdir\x07"
    mock_proc.readAllStandardOutput.return_value.data.return_value = osc7
    tp._proc = mock_proc

    tp._read_out()

    assert received == [Path("/tmp/testdir")]


# F254 — User Action Output Capture
def test_run_command_writes_to_running_process(qtbot):
    from biome_fm.qt import QProcess
    from biome_fm.views.terminal_panel import TerminalPanel
    tp = TerminalPanel()
    qtbot.addWidget(tp)

    mock_proc = MagicMock()
    mock_proc.state.return_value = QProcess.ProcessState.Running
    tp._proc = mock_proc

    tp.run_command("echo hello")

    mock_proc.write.assert_called_once_with(b"echo hello\n")


def test_run_command_starts_process_if_not_started(qtbot, tmp_path):
    from biome_fm.views.terminal_panel import TerminalPanel
    tp = TerminalPanel()
    qtbot.addWidget(tp)
    assert tp._proc is None
    # run_command should start the shell (may not complete in test env, but _proc must be set)
    tp.run_command("echo hello", cwd=tmp_path)
    assert tp._proc is not None
