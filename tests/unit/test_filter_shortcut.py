"""Test Ctrl+F activates FilterBar — unit (no Qt widgets instantiated)."""
from unittest.mock import MagicMock

from biome_fm.views.filter_bar import FilterBar


def test_filter_bar_activate_shows_and_focuses():
    bar = FilterBar.__new__(FilterBar)
    bar._edit = MagicMock()
    bar.show = MagicMock()
    bar.activate()
    bar.show.assert_called_once()
    bar._edit.setFocus.assert_called_once()
    bar._edit.selectAll.assert_called_once()


def test_filter_bar_deactivate_clears_and_hides():
    bar = FilterBar.__new__(FilterBar)
    bar._edit = MagicMock()
    bar.hide = MagicMock()
    bar.closed = MagicMock()
    bar.deactivate()
    bar._edit.clear.assert_called_once()
    bar.hide.assert_called_once()
    bar.closed.emit.assert_called_once()
