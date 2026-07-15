"""Integration tests — '+' tab button in PaneView nav bar, toolbar removal."""
import pytest
from biome_fm.views.pane_view import PaneView
from biome_fm.qt import QToolBar
from biome_fm.views.main_window import MainWindow


@pytest.fixture
def pane(qtbot):
    w = PaneView()
    qtbot.addWidget(w)
    return w


def test_plus_button_exists(pane):
    """'+' button exists on PaneView nav bar."""
    assert hasattr(pane, "_btn_new_tab")
    assert pane._btn_new_tab.text() == "+"


def test_plus_button_emits_signal(pane, qtbot):
    """Clicking '+' emits new_tab_requested."""
    with qtbot.waitSignal(pane.new_tab_requested, timeout=500):
        pane._btn_new_tab.click()


def test_plus_button_in_nav_bar(pane):
    """'+' button shares nav-widget parent with nav_back button."""
    nav_back = pane.findChild(type(pane._btn_new_tab), "nav_back")
    assert pane._btn_new_tab.parent() == nav_back.parent()


def test_toolbar_has_no_actions(qtbot):
    """MainWindow toolbar (if present) has no user actions."""
    win = MainWindow()
    qtbot.addWidget(win)
    for tb in win.findChildren(QToolBar):
        assert tb.actions() == []
