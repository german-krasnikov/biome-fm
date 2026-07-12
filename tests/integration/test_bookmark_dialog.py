"""Integration tests for BookmarkDialog."""
from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.views.bookmark_dialog import BookmarkDialog


@pytest.fixture
def store(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/a"))
    s.add(Path("/b"))
    s.add(Path("/c"))
    return s


@pytest.fixture
def dialog(qtbot, store):
    d = BookmarkDialog(store)
    qtbot.addWidget(d)
    return d


def test_dialog_lists_all_bookmarks(dialog, store):
    assert dialog._list.count() == len(store.all())


def test_remove_deletes_from_store(dialog, store):
    dialog._list.setCurrentRow(0)
    dialog._on_remove()
    assert dialog._list.count() == 2
    assert len(store.all()) == 2


def test_move_up_reorders(dialog, store):
    dialog._list.setCurrentRow(1)
    original = store.all()[1]
    dialog._on_up()
    assert store.all()[0] == original


def test_move_down_reorders(dialog, store):
    dialog._list.setCurrentRow(0)
    original = store.all()[0]
    dialog._on_down()
    assert store.all()[1] == original
