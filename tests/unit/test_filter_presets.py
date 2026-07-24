"""Unit tests for FILTER_PRESETS constant — no Qt required."""
from biome_fm.views.filter_bar import FILTER_PRESETS


def test_presets_non_empty():
    assert len(FILTER_PRESETS) >= 1


def test_presets_are_pairs_of_strings():
    for name, text in FILTER_PRESETS:
        assert isinstance(name, str) and name
        assert isinstance(text, str) and text

