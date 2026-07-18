"""Unit tests for F219 — Hotlist grouped_items()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.models.bookmark_node import BookmarkNode
from biome_fm.presenters.hotlist import Hotlist


def _entry(p: str) -> MagicMock:
    e = MagicMock()
    e.path = Path(p)
    return e


def test_grouped_items_has_recent_section():
    store = MagicMock()
    store.top.return_value = [_entry("/a"), _entry("/b")]
    h = Hotlist(store)
    groups = h.grouped_items()
    assert any(n.kind == "submenu" and n.name == "Recent" for n in groups)


def test_grouped_items_recent_children_match_frecency():
    store = MagicMock()
    store.top.return_value = [_entry("/home/user"), _entry("/tmp")]
    h = Hotlist(store)
    groups = h.grouped_items()
    recent = next(n for n in groups if n.name == "Recent")
    paths = [c.path for c in recent.children]
    assert Path("/home/user") in paths
    assert Path("/tmp") in paths


def test_grouped_items_includes_bookmarks():
    store = MagicMock()
    store.top.return_value = []
    bm = MagicMock()
    bm.tree.return_value = [BookmarkNode(kind="dir", path=Path("/home"), name="Home")]
    h = Hotlist(store)
    groups = h.grouped_items(bookmark_store=bm)
    bm_group = next((n for n in groups if n.kind == "submenu" and n.name == "Bookmarks"), None)
    assert bm_group is not None
    assert any(c.path == Path("/home") for c in bm_group.children)


def test_grouped_items_no_bookmark_store_omits_bookmarks_section():
    store = MagicMock()
    store.top.return_value = []
    h = Hotlist(store)
    groups = h.grouped_items()
    assert not any(n.name == "Bookmarks" for n in groups)
