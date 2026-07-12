"""Unit tests for BookmarkStore. No Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore


@pytest.fixture
def store(tmp_path):
    return BookmarkStore(tmp_path / "bookmarks.toml")


class TestBookmarkStore:
    def test_add_bookmark(self, store):
        store.add(Path("/home/user"))
        assert Path("/home/user") in store.all()

    def test_remove_bookmark(self, store):
        store.add(Path("/home/user"))
        store.remove(Path("/home/user"))
        assert Path("/home/user") not in store.all()

    def test_persist_and_load(self, tmp_path):
        p = tmp_path / "bm.toml"
        s1 = BookmarkStore(p)
        s1.add(Path("/persist/me"))
        s2 = BookmarkStore(p)
        assert Path("/persist/me") in s2.all()

    def test_load_missing_file(self, tmp_path):
        s = BookmarkStore(tmp_path / "missing.toml")
        assert s.all() == []

    def test_dedup(self, store):
        store.add(Path("/dup"))
        store.add(Path("/dup"))
        assert store.all().count(Path("/dup")) == 1

    def test_order_preserved(self, store):
        paths = [Path(f"/p{i}") for i in range(5)]
        for p in paths:
            store.add(p)
        assert store.all() == paths

    def test_move_up(self, tmp_path):
        s = BookmarkStore(tmp_path / "bm.toml")
        s.add(Path("/a")); s.add(Path("/b")); s.add(Path("/c"))
        s.move_up(Path("/b"))
        items = s.all()
        assert items.index(Path("/b")) < items.index(Path("/a"))

    def test_move_up_at_top_noop(self, tmp_path):
        s = BookmarkStore(tmp_path / "bm.toml")
        s.add(Path("/a")); s.add(Path("/b"))
        first = s.all()[0]
        s.move_up(first)
        assert s.all()[0] == first

    def test_move_down(self, tmp_path):
        s = BookmarkStore(tmp_path / "bm.toml")
        s.add(Path("/a")); s.add(Path("/b")); s.add(Path("/c"))
        s.move_down(Path("/b"))
        items = s.all()
        assert items.index(Path("/b")) > items.index(Path("/c"))

    def test_replace(self, tmp_path):
        s = BookmarkStore(tmp_path / "bm.toml")
        s.add(Path("/a")); s.add(Path("/b"))
        s.replace(Path("/a"), Path("/x"))
        assert Path("/x") in s
        assert Path("/a") not in s
