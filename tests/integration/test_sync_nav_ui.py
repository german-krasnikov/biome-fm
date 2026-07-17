"""Integration tests — sync browsing visual indicator on PaneSideView."""
import pytest
from biome_fm.views.pane_side_view import PaneSideView


@pytest.fixture
def side(qtbot):
    w = PaneSideView()
    qtbot.addWidget(w)
    w.show()
    return w


def test_sync_indicator_hidden_by_default(side):
    """Sync indicator label is hidden at startup."""
    assert not side._sync_label.isVisible()


def test_sync_indicator_shown_when_active(side):
    """set_sync_indicator(True) makes the label visible."""
    side.set_sync_indicator(True)
    assert side._sync_label.isVisible()


def test_sync_indicator_hidden_when_inactive(side):
    """set_sync_indicator(False) hides the label."""
    side.set_sync_indicator(True)
    side.set_sync_indicator(False)
    assert not side._sync_label.isVisible()
