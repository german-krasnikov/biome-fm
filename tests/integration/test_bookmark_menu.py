"""Integration tests for BookmarkMenu widget."""
from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.views.bookmark_menu import BookmarkMenu


@pytest.fixture
def store(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/home/user/Documents"))
    s.add(Path("/tmp"))
    return s


@pytest.fixture
def menu(qtbot, store):
    w = BookmarkMenu()
    w.set_store(store)
    qtbot.addWidget(w)
    return w


def test_menu_rebuilds_with_bookmarks(menu):
    menu._rebuild()
    # 2 bookmarks + separator + "Edit Bookmarks..." = 4 actions
    assert len(menu._menu.actions()) == 4


def test_bookmark_chosen_emits_path(menu, qtbot):
    menu._rebuild()
    with qtbot.waitSignal(menu.bookmark_chosen) as sig:
        menu._menu.actions()[0].trigger()
    assert isinstance(sig.args[0], Path)


def test_edit_action_emits_signal(menu, qtbot):
    menu._rebuild()
    with qtbot.waitSignal(menu.edit_requested):
        menu._menu.actions()[-1].trigger()  # "Edit Bookmarks..."


def test_empty_store_only_edit(qtbot, tmp_path):
    s = BookmarkStore(tmp_path / "empty.toml")
    w = BookmarkMenu()
    w.set_store(s)
    qtbot.addWidget(w)
    w._rebuild()
    # separator + "Edit Bookmarks..." = 2 actions
    assert len(w._menu.actions()) == 2
