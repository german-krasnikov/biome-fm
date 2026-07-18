"""Unit tests for BookmarkStore numbered slots (F049)."""
from pathlib import Path
import pytest
from biome_fm.models.bookmark_store import BookmarkStore


@pytest.fixture
def store(tmp_path):
    return BookmarkStore(tmp_path / "bookmarks.toml")


def test_set_numbered_bookmark(store, tmp_path):
    store.set_numbered(1, tmp_path)
    assert store.get_numbered(1) == tmp_path


def test_get_unset_slot_returns_none(store):
    assert store.get_numbered(5) is None


def test_nine_slots_max(store, tmp_path):
    with pytest.raises(ValueError):
        store.set_numbered(0, tmp_path)
    with pytest.raises(ValueError):
        store.set_numbered(10, tmp_path)
    # valid extremes should not raise
    store.set_numbered(1, tmp_path)
    store.set_numbered(9, tmp_path)


def test_clear_numbered_bookmark(store, tmp_path):
    store.set_numbered(3, tmp_path)
    store.clear_numbered(3)
    assert store.get_numbered(3) is None


def test_overwrite_slot(store, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    store.set_numbered(1, tmp_path)
    store.set_numbered(1, other)
    assert store.get_numbered(1) == other
