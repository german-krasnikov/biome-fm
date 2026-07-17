from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.git.status_cache import GitStatusCache, RepoStatus


# ---------------------------------------------------------------------------
# find_repo
# ---------------------------------------------------------------------------


def test_find_repo_walks_up(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    src = repo / "src"
    src.mkdir()
    cache = GitStatusCache()
    assert cache.find_repo(src) == repo


def test_find_repo_no_git_returns_none(tmp_path):
    cache = GitStatusCache()
    assert cache.find_repo(tmp_path) is None


# ---------------------------------------------------------------------------
# _parse
# ---------------------------------------------------------------------------


def _parse(output: str, root: Path) -> RepoStatus:
    return GitStatusCache._parse(output, root)


def test_parse_modified(tmp_path):
    (tmp_path / "src").mkdir()
    result = _parse(" M src/foo.py\n", tmp_path)
    assert result.statuses[(tmp_path / "src" / "foo.py").resolve()] == " M"


def test_parse_untracked(tmp_path):
    result = _parse("?? new.txt\n", tmp_path)
    assert result.statuses[(tmp_path / "new.txt").resolve()] == "??"


def test_parse_added(tmp_path):
    result = _parse("A  staged.py\n", tmp_path)
    assert result.statuses[(tmp_path / "staged.py").resolve()] == "A "


def test_parse_renamed(tmp_path):
    result = _parse("R  old.py -> new.py\n", tmp_path)
    assert result.statuses[(tmp_path / "new.py").resolve()] == "R "


def test_parse_dirty_dir_rollup(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    result = _parse("?? a/b/c.py\n", tmp_path)
    assert (tmp_path / "a" / "b").resolve() in result.dirty_dirs
    assert (tmp_path / "a").resolve() in result.dirty_dirs


# ---------------------------------------------------------------------------
# get_status / _fetch error handling
# ---------------------------------------------------------------------------


def _make_proc(stdout: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.returncode = returncode
    return proc


def test_git_not_installed(tmp_path):
    (tmp_path / ".git").mkdir()
    cache = GitStatusCache()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = cache.get_status(tmp_path)
    assert result.statuses == {}
    assert result.dirty_dirs == frozenset()


def test_ttl_caches(tmp_path):
    (tmp_path / ".git").mkdir()
    cache = GitStatusCache()
    with patch("subprocess.run", return_value=_make_proc()) as mock_run:
        cache.get_status(tmp_path)
        cache.get_status(tmp_path)
    assert mock_run.call_count == 1


def test_invalidate_clears_cache(tmp_path):
    (tmp_path / ".git").mkdir()
    cache = GitStatusCache()
    with patch("subprocess.run", return_value=_make_proc()) as mock_run:
        cache.get_status(tmp_path)
        cache.invalidate(tmp_path)
        cache.get_status(tmp_path)
    assert mock_run.call_count == 2


# ---------------------------------------------------------------------------
# file_status / dir_is_dirty
# ---------------------------------------------------------------------------


def test_file_status_returns_xy(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "src").mkdir()
    cache = GitStatusCache()
    with patch("subprocess.run", return_value=_make_proc(" M src/foo.py\n")):
        result = cache.file_status(repo / "src" / "foo.py")
    assert result == " M"


def test_file_status_clean_returns_none(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    cache = GitStatusCache()
    with patch("subprocess.run", return_value=_make_proc("")):
        result = cache.file_status(repo / "clean.py")
    assert result is None
