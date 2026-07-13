"""Integration tests for BookmarkMenu with recursive tree nodes."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.views.bookmark_menu import BookmarkMenu


class _StubStore:
    def __init__(self, nodes: list[BookmarkNode]) -> None:
        self._nodes = nodes

    def tree(self) -> list[BookmarkNode]:
        return self._nodes

    def all(self) -> list[Path]:
        def _flat(nodes):
            for n in nodes:
                if n.kind == "dir" and n.path:
                    yield n.path
                elif n.kind == "submenu":
                    yield from _flat(n.children)
        return list(_flat(self._nodes))


@pytest.fixture
def menu(qtbot):
    w = BookmarkMenu()
    qtbot.addWidget(w)
    return w


def _submenus(m: BookmarkMenu):
    return [(a, a.menu()) for a in m._menu.actions() if a.menu() is not None]


def _flat_non_sep(m: BookmarkMenu):
    return [a for a in m._menu.actions() if a.menu() is None and not a.isSeparator()]


# ── 1. flat dirs ──────────────────────────────────────────────────────────────

def test_flat_dirs_show_as_actions(menu):
    store = _StubStore([
        BookmarkNode("dir", Path("/a"), "Alpha"),
        BookmarkNode("dir", Path("/b"), "Beta"),
    ])
    menu.set_store(store)
    menu._rebuild()
    non_sep = _flat_non_sep(menu)
    # 2 dirs + "Edit Bookmarks..." = 3 non-separator flat actions
    assert len(non_sep) == 3
    assert any(a.text() == "Edit Bookmarks..." for a in non_sep)


# ── 2. submenu ────────────────────────────────────────────────────────────────

def test_submenu_appears_as_cascading_menu(menu):
    store = _StubStore([
        BookmarkNode("submenu", name="Work", children=[
            BookmarkNode("dir", Path("/work/a"), "Proj A"),
        ]),
    ])
    menu.set_store(store)
    menu._rebuild()
    subs = _submenus(menu)
    assert len(subs) == 1
    assert subs[0][0].text() == "Work"


# ── 3. separator ──────────────────────────────────────────────────────────────

def test_separator_renders_as_menu_separator(menu):
    store = _StubStore([
        BookmarkNode("dir", Path("/a"), "A"),
        BookmarkNode("separator"),
        BookmarkNode("dir", Path("/b"), "B"),
    ])
    menu.set_store(store)
    menu._rebuild()
    separators = [a for a in menu._menu.actions() if a.isSeparator()]
    # at least 2: the explicit one + the one before "Edit Bookmarks..."
    assert len(separators) >= 2


# ── 4. nested submenus ────────────────────────────────────────────────────────

def test_nested_submenu_two_levels(menu):
    store = _StubStore([
        BookmarkNode("submenu", name="Outer", children=[
            BookmarkNode("submenu", name="Inner", children=[
                BookmarkNode("dir", Path("/deep"), "Deep"),
            ]),
        ]),
    ])
    menu.set_store(store)
    menu._rebuild()
    outer_subs = _submenus(menu)  # keep alive
    assert len(outer_subs) == 1
    _outer_act, outer_menu = outer_subs[0]
    inner_subs = [(a, a.menu()) for a in outer_menu.actions() if a.menu() is not None]
    assert len(inner_subs) == 1
    assert inner_subs[0][0].text() == "Inner"


# ── 5. dir action emits signal ────────────────────────────────────────────────

def test_dir_action_emits_bookmark_chosen(menu, qtbot):
    p = Path("/x/y")
    store = _StubStore([BookmarkNode("dir", p, "XY")])
    menu.set_store(store)
    menu._rebuild()
    actions = _flat_non_sep(menu)
    dir_act = next(a for a in actions if a.text() == "XY")
    with qtbot.waitSignal(menu.bookmark_chosen) as sig:
        dir_act.trigger()
    assert sig.args[0] == p


# ── 6. submenu child emits signal ────────────────────────────────────────────

def test_submenu_child_emits_bookmark_chosen(menu, qtbot):
    p = Path("/sub/child")
    store = _StubStore([
        BookmarkNode("submenu", name="Grp", children=[
            BookmarkNode("dir", p, "Child"),
        ]),
    ])
    menu.set_store(store)
    menu._rebuild()
    subs = _submenus(menu)  # keep alive to prevent GC of submenu
    _act, sub_menu = subs[0]
    child_act = next(a for a in sub_menu.actions() if not a.isSeparator() and a.text() == "Child")
    with qtbot.waitSignal(menu.bookmark_chosen) as sig:
        child_act.trigger()
    assert sig.args[0] == p


# ── 7. empty submenu no crash ─────────────────────────────────────────────────

def test_empty_submenu_no_crash(menu):
    store = _StubStore([BookmarkNode("submenu", name="Empty", children=[])])
    menu.set_store(store)
    menu._rebuild()  # must not raise
    subs = _submenus(menu)
    assert len(subs) == 1


# ── 8. edit action always present ────────────────────────────────────────────

def test_edit_action_always_present(menu):
    store = _StubStore([])
    menu.set_store(store)
    menu._rebuild()
    all_actions = menu._menu.actions()
    assert any(a.text() == "Edit Bookmarks..." for a in all_actions)
