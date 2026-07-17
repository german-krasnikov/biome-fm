"""Tests for SearchScope — TDD, no Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.search_presenter import SearchMode, SearchPresenter, SearchScope


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """
    root/
      root_file.txt
      sub/
        nested.txt
    """
    (tmp_path / "root_file.txt").write_text("root")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested")
    return tmp_path


def test_subtree_finds_nested(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(
        "*.txt", scope=SearchScope.SUBTREE
    )
    names = {r.item.name for r in results}
    assert "nested.txt" in names


def test_current_dir_skips_subdirs(tree: Path) -> None:
    results = SearchPresenter(LocalVFS(), tree).search(
        "*.txt", scope=SearchScope.CURRENT_DIR
    )
    names = {r.item.name for r in results}
    assert "root_file.txt" in names
    assert "nested.txt" not in names
