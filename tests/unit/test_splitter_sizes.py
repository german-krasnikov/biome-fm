"""Unit tests for splitter size padding logic (no Qt)."""
from biome_fm.app import _pad_sizes


def test_pad_sizes_uses_saved():
    assert _pad_sizes([600, 400], 5) == [600, 400, 0, 0, 0]


def test_pad_sizes_with_exact_count():
    assert _pad_sizes([100, 200, 0, 0, 0], 5) == [100, 200, 0, 0, 0]


def test_pad_sizes_with_long_list():
    # truncates to count
    assert _pad_sizes([1, 2, 3, 4, 5, 6], 5) == [1, 2, 3, 4, 5]


def test_pad_sizes_empty_defaults_to_zeros():
    assert _pad_sizes([], 5) == [0, 0, 0, 0, 0]


def test_pad_sizes_single_value():
    assert _pad_sizes([800], 5) == [800, 0, 0, 0, 0]
