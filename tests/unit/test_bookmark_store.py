"""Unit tests for BookmarkStore. No Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_store import BookmarkStore


@pytest.fixture
def store(tmp_path):
    p = tmp_path / "bookmarks.toml"
    p.write_text("[bookmarks]\npaths = []\n")
    return BookmarkStore(p)


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

    def test_load_missing_file_has_defaults(self, tmp_path):
        s = BookmarkStore(tmp_path / "missing.toml")
        defaults = [p for p in s._default_paths() if p.is_dir()]
        assert s.all() == defaults

    def test_dedup(self, store):
        store.add(Path("/dup"))
        store.add(Path("/dup"))
        assert store.all().count(Path("/dup")) == 1

    def test_order_preserved(self, store):
        paths = [Path(f"/p{i}") for i in range(5)]
        for p in paths:
            store.add(p)
        assert store.all() == paths



# ── Display name tests ─────────────────────────────────────────────────────

def test_add_with_name(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/a"), name="Work")
    assert s.get_name(Path("/a")) == "Work"


def test_display_label_with_name(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/a"), name="My Dir")
    assert s.display_label(Path("/a")) == "My Dir"


def test_display_label_without_name(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/a"))
    assert s.display_label(Path("/a")) == "a"


def test_display_label_defaults_to_folder_name(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    p = Path("/home/user/Documents")
    s.add(p)
    assert s.display_label(p) == "Documents"


def test_display_label_root_path_fallback(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    p = Path("/")
    s.add(p)
    assert s.display_label(p) == "/"


def test_display_label_custom_name_wins(tmp_path):
    s = BookmarkStore(tmp_path / "bm.toml")
    s.add(Path("/code"))
    s.set_name(Path("/code"), "Work")
    assert s.display_label(Path("/code")) == "Work"


def test_set_name_persists(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    s1.add(Path("/x"))
    s1.set_name(Path("/x"), "Renamed")
    s2 = BookmarkStore(p)
    assert s2.get_name(Path("/x")) == "Renamed"


def test_migration_old_format(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text('[bookmarks]\npaths = ["/a", "/b"]\n')
    s = BookmarkStore(p)
    assert s.all() == [Path("/a"), Path("/b")]
    assert s.get_name(Path("/a")) == ""


def test_name_with_quotes_roundtrip(tmp_path):
    p = tmp_path / "bm.toml"
    s1 = BookmarkStore(p)
    s1.add(Path("/a"), name='My "Work" folder')
    s2 = BookmarkStore(p)
    assert s2.get_name(Path("/a")) == 'My "Work" folder'


def test_corrupt_toml_does_not_crash(tmp_path):
    p = tmp_path / "bm.toml"
    p.write_text("invalid toml {{{{")
    s = BookmarkStore(p)
    assert s.all() == []
