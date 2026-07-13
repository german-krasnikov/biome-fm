"""Integration tests for BookmarkDialog (QTreeWidget)."""
from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.views.bookmark_dialog import BookmarkDialog, _PATH_ROLE
from biome_fm.qt import Qt


@pytest.fixture
def store(tmp_path):
    bm_path = tmp_path / "bm.toml"
    bm_path.write_text("[bookmarks]\npaths = []\n")
    s = BookmarkStore(bm_path)
    s.add(Path("/a"))
    s.add(Path("/b"))
    s.add(Path("/c"))
    return s


@pytest.fixture
def dialog(qtbot, store):
    d = BookmarkDialog(store)
    qtbot.addWidget(d)
    return d


def _select(dialog, idx: int) -> None:
    dialog._tree.setCurrentItem(dialog._tree.topLevelItem(idx))


def test_dialog_lists_all_bookmarks(dialog, store):
    assert dialog._tree.topLevelItemCount() == len(store.all())


def test_remove_deletes_from_store(dialog, store):
    _select(dialog, 0)
    dialog._on_remove()
    assert dialog._tree.topLevelItemCount() == 2
    assert len(store.all()) == 2


def test_move_up_reorders(dialog, store):
    _select(dialog, 1)
    original = store.all()[1]
    dialog._move(-1)
    assert store.all()[0] == original


def test_move_down_reorders(dialog, store):
    _select(dialog, 0)
    original = store.all()[0]
    dialog._move(1)
    assert store.all()[1] == original


# ── Attribute / window type tests ─────────────────────────────────────────────

def test_dialog_has_add_button(dialog):
    assert hasattr(dialog, "_btn_add")


def test_dialog_is_tool_window(dialog):
    assert dialog.windowFlags() & Qt.WindowType.Tool


# ── Add ───────────────────────────────────────────────────────────────────────

def test_add_button_adds_path(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("/new/path", True)))
    dialog._on_add()
    assert Path("/new/path") in store.all()


def test_add_button_cancel_noop(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    before = list(store.all())
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("", False)))
    dialog._on_add()
    assert list(store.all()) == before


def test_add_tilde_expansion(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("~/Documents", True)))
    dialog._on_add()
    assert Path.home() / "Documents" in store.all()


# ── Drop ──────────────────────────────────────────────────────────────────────

def test_drop_biome_mime(dialog, store):
    from PySide6.QtCore import QMimeData
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", b"/drop/alpha\n/drop/beta")
    dialog._handle_drop(mime)
    assert Path("/drop/alpha") in store.all()
    assert Path("/drop/beta") in store.all()


def test_drop_url_list(dialog, store, tmp_path):
    from PySide6.QtCore import QMimeData, QUrl
    target = tmp_path / "dropped"
    target.mkdir()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(target))])
    dialog._handle_drop(mime)
    assert target in store.all()


def test_empty_drop_no_publish(dialog, store):
    from PySide6.QtCore import QMimeData
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", b"")
    before = list(store.all())
    dialog._handle_drop(mime)
    assert list(store.all()) == before


def test_duplicate_drop_no_publish(dialog, store):
    from PySide6.QtCore import QMimeData
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", b"/a")
    before = list(store.all())
    dialog._handle_drop(mime)
    assert list(store.all()) == before


# ── Rename ────────────────────────────────────────────────────────────────────

def test_rename_button_exists(dialog):
    assert hasattr(dialog, "_btn_rename")


def test_rename_updates_store(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("Alias", True)))
    _select(dialog, 0)
    dialog._on_rename()
    assert store.get_name(store.all()[0]) == "Alias"


# ── Label display ─────────────────────────────────────────────────────────────

def test_add_shows_folder_name_in_list(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText",
                        staticmethod(lambda *a, **kw: ("/home/user/Documents", True)))
    dialog._on_add()
    for i in range(dialog._tree.topLevelItemCount()):
        item = dialog._tree.topLevelItem(i)
        if item.data(0, _PATH_ROLE) == "/home/user/Documents":
            assert "Documents" in item.text(0)
            break
    else:
        pytest.fail("Added bookmark not found in tree")


def test_dnd_shows_folder_name_in_list(dialog, store):
    from PySide6.QtCore import QMimeData
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", b"/home/user/Projects")
    dialog._handle_drop(mime)
    for i in range(dialog._tree.topLevelItemCount()):
        item = dialog._tree.topLevelItem(i)
        if item.data(0, _PATH_ROLE) == "/home/user/Projects":
            assert "Projects" in item.text(0)
            break
    else:
        pytest.fail("Dropped bookmark not found in tree")
