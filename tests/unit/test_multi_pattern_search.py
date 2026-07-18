"""Unit tests for multi-pattern (semicolon-separated) NAME_WILDCARD search."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter


def _make_item(name: str) -> FileItem:
    item = MagicMock(spec=FileItem)
    item.name = name
    item.is_dir = False
    item.path = Path(f"/tmp/{name}")
    item.size = 0
    return item


def _presenter() -> SearchPresenter:
    vfs = MagicMock()
    return SearchPresenter(vfs, Path("/tmp"))


class TestMultiPatternSearch:
    def test_two_patterns_match(self):
        p = _presenter()
        assert p._match(_make_item("foo.py"), "*.py;*.ts", SearchMode.NAME_WILDCARD) is not None
        assert p._match(_make_item("bar.ts"), "*.py;*.ts", SearchMode.NAME_WILDCARD) is not None

    def test_neither_pattern_no_match(self):
        p = _presenter()
        assert p._match(_make_item("baz.txt"), "*.py;*.ts", SearchMode.NAME_WILDCARD) is None

    def test_single_pattern_unchanged(self):
        p = _presenter()
        assert p._match(_make_item("hello.py"), "*.py", SearchMode.NAME_WILDCARD) is not None
        assert p._match(_make_item("hello.js"), "*.py", SearchMode.NAME_WILDCARD) is None

    def test_whitespace_trimmed(self):
        p = _presenter()
        assert p._match(_make_item("foo.py"), "*.py ; *.ts", SearchMode.NAME_WILDCARD) is not None
        assert p._match(_make_item("bar.ts"), "*.py ; *.ts", SearchMode.NAME_WILDCARD) is not None

    def test_empty_pattern_ignored(self):
        p = _presenter()
        assert p._match(_make_item("foo.py"), "*.py;;", SearchMode.NAME_WILDCARD) is not None
        assert p._match(_make_item("baz.txt"), "*.py;;", SearchMode.NAME_WILDCARD) is None
