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


def test_tab_bar_not_movable(qtbot):
    """C26: tab bar must not be movable (tabMoved is not wired)."""
    side = PaneSideView()
    qtbot.addWidget(side)
    assert side._tab_bar.isMovable() is False


def test_lock_glyph_stable_after_close_left_tab(qtbot):
    """C26: _locked indices shift so set_tab_title re-applies glyph correctly."""
    side = PaneSideView()
    qtbot.addWidget(side)
    side.add_tab("A")
    side.new_pane()
    side.add_tab("B")
    side.new_pane()
    side.add_tab("C")
    side.new_pane()
    # Lock the third tab (idx=2), then close the first (idx=0)
    side._tab_bar.set_locked(2, True)
    side.remove_tab(0)
    # Simulate a navigation update that rebuilds the tab title for the newly-active tab
    # (idx 1 = what was idx 2 before removal). Without index shift, _locked still has
    # {2} not {1}, so set_tab_title won't prepend the lock glyph.
    side.set_tab_title(1, "/some/locked/path")
    assert side._tab_bar.tabText(1).startswith("🔒")
