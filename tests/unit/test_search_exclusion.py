"""Unit tests for search exclusion patterns (F006)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import DEFAULT_EXCLUDE, SearchMode, SearchPresenter

_ROOT = Path("/root")


def _file(name: str, parent: Path = _ROOT) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=False, size=10, modified=0.0)


def _dir(name: str, parent: Path = _ROOT) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=True, size=0, modified=0.0)


def _vfs(tree: dict) -> object:
    vfs = MagicMock()
    vfs.listdir.side_effect = lambda p: tree.get(p, [])
    return vfs


# ---------------------------------------------------------------------------


def test_node_modules_skipped() -> None:
    nm = _ROOT / "node_modules"
    tree = {
        _ROOT: [_dir("node_modules"), _file("app.js")],
        nm: [_file("big.js", nm)],
    }
    results = SearchPresenter(_vfs(tree), _ROOT).search("*.js", SearchMode.NAME_WILDCARD)
    names = [r.item.name for r in results]
    assert "big.js" not in names
    assert "app.js" in names


def test_git_dir_skipped() -> None:
    git = _ROOT / ".git"
    tree = {
        _ROOT: [_dir(".git"), _file("README.md")],
        git: [_file("config", git)],
    }
    results = SearchPresenter(_vfs(tree), _ROOT).search("config", SearchMode.NAME_WILDCARD)
    assert not results


def test_custom_exclude_pattern() -> None:
    build = _ROOT / "build"
    tree = {
        _ROOT: [_dir("build"), _dir("src"), _file("main.py")],
        build: [_file("output.o", build)],
        _ROOT / "src": [_file("lib.py", _ROOT / "src")],
    }
    results = SearchPresenter(_vfs(tree), _ROOT).search(
        "*.py", SearchMode.NAME_WILDCARD, exclude_patterns=["build"]
    )
    names = [r.item.name for r in results]
    assert "output.o" not in names
    assert "lib.py" in names


def test_exclude_empty_list_searches_everything() -> None:
    nm = _ROOT / "node_modules"
    tree = {
        _ROOT: [_dir("node_modules"), _file("app.js")],
        nm: [_file("big.js", nm)],
    }
    results = SearchPresenter(_vfs(tree), _ROOT).search(
        "*.js", SearchMode.NAME_WILDCARD, exclude_patterns=[]
    )
    names = [r.item.name for r in results]
    assert "big.js" in names
    assert "app.js" in names


def test_fnmatch_wildcard_exclude() -> None:
    cache_dir = _ROOT / ".eslint.cache"
    tree = {
        _ROOT: [_dir(".eslint.cache"), _file("index.js")],
        cache_dir: [_file("data.json", cache_dir)],
    }
    results = SearchPresenter(_vfs(tree), _ROOT).search(
        "data.json", SearchMode.NAME_WILDCARD, exclude_patterns=["*.cache"]
    )
    assert not results


def test_default_exclude_list_is_populated() -> None:
    assert ".git" in DEFAULT_EXCLUDE
    assert "node_modules" in DEFAULT_EXCLUDE
    assert "__pycache__" in DEFAULT_EXCLUDE
