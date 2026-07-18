"""F297 — Git changed files virtual pane."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.git.status_cache import GitStatusCache, RepoStatus
from biome_fm.git.virtual_pane import git_changed_files


def _make_status(paths: list[str], root: Path) -> RepoStatus:
    statuses = {(root / p).resolve(): " M" for p in paths}
    return RepoStatus(statuses=statuses, dirty_dirs=frozenset(), fetched_at=0.0)


def test_git_changed_files_builds_items(tmp_path):
    cache = MagicMock(spec=GitStatusCache)
    cache.get_status.return_value = _make_status(["a.py", "b.py"], tmp_path)
    items = git_changed_files(tmp_path, cache)
    assert len(items) == 2
    names = {i.name for i in items}
    assert names == {"a.py", "b.py"}
    assert all(not i.is_dir for i in items)


def test_empty_status_returns_empty_list(tmp_path):
    cache = MagicMock(spec=GitStatusCache)
    cache.get_status.return_value = _make_status([], tmp_path)
    items = git_changed_files(tmp_path, cache)
    assert items == []
