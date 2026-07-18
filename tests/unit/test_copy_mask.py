from pathlib import Path
import pytest
from biome_fm.presenters.copy_filter import filter_by_mask

PATHS = [Path("a.jpg"), Path("b.png"), Path("c.txt"), Path("d.JPG")]


def test_mask_filters_source():
    # case-insensitive: *.jpg matches both a.jpg and d.JPG
    assert filter_by_mask(PATHS, "*.jpg") == [Path("a.jpg"), Path("d.JPG")]


def test_none_mask_copies_all():
    assert filter_by_mask(PATHS, None) == PATHS


def test_multiple_masks():
    result = filter_by_mask(PATHS, "*.jpg,*.png")
    assert result == [Path("a.jpg"), Path("b.png"), Path("d.JPG")]


def test_mask_case_insensitive():
    assert filter_by_mask(PATHS, "*.JPG") == [Path("a.jpg"), Path("d.JPG")]


def test_empty_after_filter():
    assert filter_by_mask(PATHS, "*.zip") == []
