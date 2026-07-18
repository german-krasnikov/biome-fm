"""Integration tests for PaneSideView."""
import pytest

from biome_fm.views.pane_side_view import PaneSideView
from biome_fm.views.pane_view import PaneView


@pytest.fixture
def view(qtbot):
    w = PaneSideView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_add_tab(view):
    before = view._tab_bar.count()
    view.add_tab("Tab A")
    assert view._tab_bar.count() == before + 1


def test_remove_tab(view):
    view.add_tab("Tab A")
    view.new_pane()  # keep stack in sync
    count = view._tab_bar.count()
    view.remove_tab(0)
    assert view._tab_bar.count() == count - 1


def test_new_pane_returns_pane_view(view):
    pane = view.new_pane()
    assert isinstance(pane, PaneView)


def test_set_active_tab(view):
    view.add_tab("Tab A")
    view.new_pane()
    view.add_tab("Tab B")
    view.new_pane()
    view.set_active_tab(1)
    assert view._stack.currentIndex() == 1


def test_set_tab_filter_active_appends_indicator(view):
    view.add_tab("/home/user")
    initial = view._tab_bar.tabText(0)
    view.set_tab_filter_active(0, True)
    assert view._tab_bar.tabText(0).endswith(PaneSideView._FILTER_INDICATOR)


def test_set_tab_filter_active_removes_indicator(view):
    view.add_tab("/home/user")
    view.set_tab_filter_active(0, True)
    view.set_tab_filter_active(0, False)
    text = view._tab_bar.tabText(0)
    assert PaneSideView._FILTER_INDICATOR not in text


def test_set_tab_filter_active_idempotent(view):
    """Calling active=True twice doesn't stack the indicator."""
    view.add_tab("/home/user")
    view.set_tab_filter_active(0, True)
    view.set_tab_filter_active(0, True)
    text = view._tab_bar.tabText(0)
    assert text.count(PaneSideView._FILTER_INDICATOR) == 1
