"""Integration tests for TerminalPanel widget."""
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
