"""Tests for icon-based nav buttons in PaneView."""

import pytest

from biome_fm.qt import QPushButton
from biome_fm.views.pane_view import PaneView


@pytest.fixture
def pane(qtbot):
    w = PaneView()
    qtbot.addWidget(w)
    return w


def _nav_buttons(pane: PaneView) -> list[QPushButton]:
    """Return the 4 nav buttons (first 4 QPushButtons in nav bar)."""
    return pane.findChildren(QPushButton)[:4]


def test_nav_buttons_have_icons(pane):
    for btn in _nav_buttons(pane):
        assert not btn.icon().isNull(), f"Button '{btn.text()}' has null icon"


def test_nav_buttons_no_text(pane):
    for btn in _nav_buttons(pane):
        assert btn.text() == "", f"Button should have no text, got '{btn.text()}'"
