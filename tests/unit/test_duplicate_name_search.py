"""Tests for find_duplicate_names — TDD, no Qt."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchResult, SearchScope, find_duplicate_names


def _item(name: str) -> FileItem:
    return FileItem(name=name, path=Path("/fake") / name, is_dir=False, size=0, modified=0.0)


class TestFindDuplicateNames:
    def test_find_duplicate_names_returns_intersection(self) -> None:
        left = [_item("foo.txt"), _item("bar.py"), _item("baz.md")]
        right = [_item("foo.txt"), _item("qux.rs")]
        results = find_duplicate_names(left, right)
        names = {r.item.name for r in results}
        assert names == {"foo.txt"}

    def test_find_duplicate_names_empty(self) -> None:
        assert find_duplicate_names([], []) == []

    def test_find_duplicate_names_no_overlap(self) -> None:
        left = [_item("a.txt"), _item("b.py")]
        right = [_item("c.txt"), _item("d.rs")]
        assert find_duplicate_names(left, right) == []

    def test_duplicate_names_scope_exists(self) -> None:
        assert hasattr(SearchScope, "DUPLICATE_NAMES")
