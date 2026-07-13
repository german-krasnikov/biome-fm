"""Integration tests for BookmarkDialog with tree nodes (QTreeWidget)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.views.bookmark_dialog import BookmarkDialog, _KIND_ROLE, _PATH_ROLE
from biome_fm.qt import Qt


class _StubStore:
    """Minimal store stub for tree tests — no filesystem."""

    def __init__(self, nodes: list[BookmarkNode]) -> None:
        self._nodes = nodes

    def tree(self) -> list[BookmarkNode]:
        return list(self._nodes)

    def set_tree(self, nodes: list[BookmarkNode]) -> None:
        self._nodes = nodes

    def all(self) -> list[Path]:
        def _flat(ns):
            for n in ns:
                if n.kind == "dir" and n.path:
                    yield n.path
                elif n.kind == "submenu":
                    yield from _flat(n.children)
        return list(_flat(self._nodes))

    def add(self, path: Path, name: str = "") -> None:
        if path not in self.all():
            self._nodes.append(BookmarkNode("dir", path, name))

    def get_name(self, path: Path) -> str:
        def _find(ns):
            for n in ns:
                if n.kind == "dir" and n.path == path:
                    return n.name
                if n.kind == "submenu":
                    r = _find(n.children)
                    if r is not None:
                        return r
            return None
        return _find(self._nodes) or ""


@pytest.fixture
def store():
    return _StubStore([
        BookmarkNode("submenu", name="Work", children=[
            BookmarkNode("dir", Path("/a"), "Proj A"),
        ]),
        BookmarkNode("dir", Path("/b"), "Home"),
        BookmarkNode("separator"),
    ])


@pytest.fixture
def dialog(qtbot, store):
    d = BookmarkDialog(store)
    qtbot.addWidget(d)
    return d


# ── 1. submenu as parent item ─────────────────────────────────────────────────

def test_tree_shows_submenu_as_parent(dialog):
    root_count = dialog._tree.topLevelItemCount()
    assert root_count == 3  # submenu + dir + separator
    top0 = dialog._tree.topLevelItem(0)
    assert top0.data(0, _KIND_ROLE) == "submenu"
    assert top0.text(0) == "Work"


# ── 2. dir inside submenu ────────────────────────────────────────────────────

def test_tree_shows_dir_inside_submenu(dialog):
    submenu_item = dialog._tree.topLevelItem(0)
    assert submenu_item.childCount() == 1
    child = submenu_item.child(0)
    assert child.data(0, _KIND_ROLE) == "dir"
    assert child.data(0, _PATH_ROLE) == "/a"


# ── 3. separator ──────────────────────────────────────────────────────────────

def test_tree_shows_separator(dialog):
    sep_item = dialog._tree.topLevelItem(2)
    assert sep_item.data(0, _KIND_ROLE) == "separator"
    assert "──" in sep_item.text(0)


# ── 4. separator not selectable ──────────────────────────────────────────────

def test_separator_not_selectable(dialog):
    sep_item = dialog._tree.topLevelItem(2)
    flags = sep_item.flags()
    assert not (flags & Qt.ItemFlag.ItemIsSelectable)


# ── 5. add submenu creates node ───────────────────────────────────────────────

def test_add_submenu_creates_node(dialog, store, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText",
                        staticmethod(lambda *a, **kw: ("NewGroup", True)))
    dialog._on_add_submenu()
    kinds = [dialog._tree.topLevelItem(i).data(0, _KIND_ROLE)
             for i in range(dialog._tree.topLevelItemCount())]
    assert "submenu" in kinds
    names = [dialog._tree.topLevelItem(i).text(0)
             for i in range(dialog._tree.topLevelItemCount())
             if dialog._tree.topLevelItem(i).data(0, _KIND_ROLE) == "submenu"]
    assert "NewGroup" in names


# ── 6. add separator creates node ────────────────────────────────────────────

def test_add_separator_creates_node(dialog):
    before = dialog._tree.topLevelItemCount()
    dialog._on_add_sep()
    after = dialog._tree.topLevelItemCount()
    assert after == before + 1
    seps = [dialog._tree.topLevelItem(i)
            for i in range(after)
            if dialog._tree.topLevelItem(i).data(0, _KIND_ROLE) == "separator"]
    assert len(seps) >= 1


# ── 7. delete removes item ───────────────────────────────────────────────────

def test_delete_removes_item(dialog, store):
    dir_item = dialog._tree.topLevelItem(1)  # dir "/b"
    dialog._tree.setCurrentItem(dir_item)
    dialog._on_remove()
    paths = store.all()
    assert Path("/b") not in paths
    assert dialog._tree.topLevelItemCount() == 2  # submenu + separator remain


# ── 8. rename updates text ───────────────────────────────────────────────────

def test_rename_updates_text(dialog, monkeypatch):
    import biome_fm.views.bookmark_dialog as mod
    monkeypatch.setattr(mod.QInputDialog, "getText",
                        staticmethod(lambda *a, **kw: ("Renamed", True)))
    submenu_item = dialog._tree.topLevelItem(0)
    dialog._tree.setCurrentItem(submenu_item)
    dialog._on_rename()
    # after refresh, find item with text "Renamed"
    found = any(
        dialog._tree.topLevelItem(i).text(0) == "Renamed"
        for i in range(dialog._tree.topLevelItemCount())
    )
    assert found


# ── 9. double-click dir emits signal ─────────────────────────────────────────

def test_double_click_dir_emits_signal(dialog, qtbot):
    dir_item = dialog._tree.topLevelItem(1)  # dir "/b"
    with qtbot.waitSignal(dialog.bookmark_chosen) as sig:
        dialog._on_double_click(dir_item)
    assert sig.args[0] == Path("/b")


# ── 10. double-click submenu no signal ───────────────────────────────────────

def test_double_click_submenu_no_signal(dialog, qtbot):
    submenu_item = dialog._tree.topLevelItem(0)
    with qtbot.assertNotEmitted(dialog.bookmark_chosen):
        dialog._on_double_click(submenu_item)
