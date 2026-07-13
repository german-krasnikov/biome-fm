"""Integration tests for BookmarkDialog."""
from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore
from biome_fm.views.bookmark_dialog import BookmarkDialog


@pytest.fixture
def store(tmp_path):
    bm_path = tmp_path / "bm.toml"
    bm_path.write_text("[bookmarks]\npaths = []\n")  # prevent default dirs being loaded
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


# ── New enhancement tests ──────────────────────────────────────────────────

def test_dialog_has_add_button(dialog):
    assert hasattr(dialog, "_btn_add")


def test_dialog_is_tool_window(dialog):
    from biome_fm.qt import Qt
    assert dialog.windowFlags() & Qt.WindowType.Tool


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


def test_rename_button_exists(dialog):
    assert hasattr(dialog, "_btn_rename")


def test_rename_updates_store(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("Alias", True)))
    dialog._list.setCurrentRow(0)
    dialog._on_rename()
    assert store.get_name(store.all()[0]) == "Alias"


def test_add_shows_folder_name_in_list(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    import pytest
    monkeypatch.setattr(mod.QInputDialog, "getText", staticmethod(lambda *a, **kw: ("/home/user/Documents", True)))
    dialog._on_add()
    from biome_fm.qt import Qt
    for i in range(dialog._list.count()):
        item = dialog._list.item(i)
        if item.data(Qt.ItemDataRole.UserRole) == "/home/user/Documents":
            assert "Documents" in item.text()
            break
    else:
        pytest.fail("Added bookmark not found in list")


def test_dnd_shows_folder_name_in_list(dialog, store):
    from PySide6.QtCore import QMimeData
    import pytest
    mime = QMimeData()
    mime.setData("application/x-biome-fm-paths", b"/home/user/Projects")
    dialog._handle_drop(mime)
    from biome_fm.qt import Qt
    for i in range(dialog._list.count()):
        item = dialog._list.item(i)
        if item.data(Qt.ItemDataRole.UserRole) == "/home/user/Projects":
            assert "Projects" in item.text()
            break
    else:
        pytest.fail("Dropped bookmark not found in list")
