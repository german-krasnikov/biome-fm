"""Integration tests for dynamic tab close button."""
import pytest
from biome_fm.views.pane_side_view import PaneSideView


@pytest.fixture
def side(qtbot):
    w = PaneSideView()
    qtbot.addWidget(w)
    return w


def test_single_tab_no_close(side):
    side.add_tab("A")
    side.new_pane()
    assert not side._tab_bar.tabsClosable()


def test_two_tabs_close_visible(side):
    side.add_tab("A"); side.new_pane()
    side.add_tab("B"); side.new_pane()
    assert side._tab_bar.tabsClosable()


def test_remove_to_one_hides_close(side):
    side.add_tab("A"); side.new_pane()
    side.add_tab("B"); side.new_pane()
    side.remove_tab(1)
    assert not side._tab_bar.tabsClosable()
