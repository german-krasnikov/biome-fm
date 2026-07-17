"""Integration tests for PatternDialog."""
import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.views.pattern_dialog import PatternDialog  # noqa: E402


def test_dialog_has_pattern_input(qtbot):
    dlg = PatternDialog()
    qtbot.addWidget(dlg)
    assert dlg._line is not None
    assert dlg._line.text() == "*"


def test_dialog_mode_select_deselect(qtbot):
    dlg = PatternDialog()
    qtbot.addWidget(dlg)
    # Both modes must be available
    modes = [dlg._mode.itemText(i) for i in range(dlg._mode.count())]
    assert "Select" in modes
    assert "Deselect" in modes
