"""Tests for macOS Touch Bar stub."""
from unittest.mock import patch


def test_noop_when_not_mac():
    with patch("biome_fm.utils.touch_bar.IS_MAC", False):
        from biome_fm.utils.touch_bar import setup_touch_bar
        setup_touch_bar(object(), [("Refresh", lambda: None)])


def test_noop_when_pyobjc_absent():
    with patch("biome_fm.utils.touch_bar.IS_MAC", True):
        from biome_fm.utils.touch_bar import setup_touch_bar
        setup_touch_bar(object(), [("Refresh", lambda: None)])


def test_empty_actions():
    from biome_fm.utils.touch_bar import setup_touch_bar
    setup_touch_bar(object(), [])
