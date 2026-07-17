"""Tests for SearchFilter — size/extension filtering."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchFilter, SearchPresenter


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    (tmp_path / "small.txt").write_bytes(b"x" * 10)
    (tmp_path / "large.txt").write_bytes(b"x" * 5000)
    (tmp_path / "readme.md").write_bytes(b"x" * 100)
    return tmp_path


def test_min_size_excludes_small(tree: Path) -> None:
    f = SearchFilter(min_size=1000)
    results = SearchPresenter(LocalVFS(), tree).search("*", filter=f)
    names = {r.item.name for r in results}
    assert "large.txt" in names
    assert "small.txt" not in names


def test_max_size_excludes_large(tree: Path) -> None:
    f = SearchFilter(max_size=200)
    results = SearchPresenter(LocalVFS(), tree).search("*", filter=f)
    names = {r.item.name for r in results}
    assert "small.txt" in names
    assert "large.txt" not in names


def test_extensions_filter(tree: Path) -> None:
    f = SearchFilter(extensions=frozenset({".md"}))
    results = SearchPresenter(LocalVFS(), tree).search("*", filter=f)
    names = {r.item.name for r in results}
    assert "readme.md" in names
    assert "small.txt" not in names
    assert "large.txt" not in names


def test_no_filter_passes_all(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search("*", filter=None)
    names = {r.item.name for r in results}
    assert {"small.txt", "large.txt", "readme.md"}.issubset(names)
