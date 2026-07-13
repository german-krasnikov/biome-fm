"""Test Ctrl+F shortcut activates FilterBar in PaneView."""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from biome_fm.views.pane_view import PaneView


@pytest.fixture
def pane_view(qtbot):
    w = PaneView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_ctrl_f_activates_filter_bar(pane_view):
    assert not pane_view.filter_bar.isVisible()
    QTest.keyPress(pane_view._table, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert pane_view.filter_bar.isVisible()


def test_escape_deactivates_filter_bar(pane_view):
    pane_view.filter_bar.activate()
    assert pane_view.filter_bar.isVisible()
    QTest.keyPress(pane_view.filter_bar._edit, Qt.Key.Key_Escape)
    assert not pane_view.filter_bar.isVisible()
