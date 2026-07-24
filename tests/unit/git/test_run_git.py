"""Unit tests for run_git() safe param and git_is_ignored()."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.git.run import git_is_ignored, run_git


# ── Scenario 1 ──────────────────────────────────────────────────────────────

def test_safe_true_swallows_oserror(tmp_path):
    with patch("subprocess.run", side_effect=OSError("no git")):
        result = run_git(["status"], cwd=tmp_path, safe=True)
    assert result == ""


# ── Scenario 2 ──────────────────────────────────────────────────────────────

def test_safe_false_reraises_oserror(tmp_path):
    with patch("subprocess.run", side_effect=OSError("no git")):
        with pytest.raises(OSError):
            run_git(["status"], cwd=tmp_path, safe=False)


# ── Scenario 3 ──────────────────────────────────────────────────────────────

def test_git_is_ignored_true_for_ignored_file(tmp_path):
    # init a real git repo so check-ignore works
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True)
    pyc = tmp_path / "foo.pyc"
    pyc.touch()
    assert git_is_ignored(pyc, tmp_path) is True


def test_git_is_ignored_false_for_tracked_file(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    regular = tmp_path / "main.py"
    regular.touch()
    assert git_is_ignored(regular, tmp_path) is False


def test_git_is_ignored_returns_false_on_oserror(tmp_path):
    with patch("subprocess.run", side_effect=OSError("no git")):
        assert git_is_ignored(tmp_path / "x.pyc", tmp_path) is False


# ── Scenario 4 ──────────────────────────────────────────────────────────────

def test_stage_files_raises_runtime_error_on_bad_path(tmp_path):
    # tmp_path is not a git repo → git add exits non-zero → RuntimeError
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    from biome_fm.git.commit_ops import stage_files
    with pytest.raises(RuntimeError):
        stage_files(tmp_path, [Path("/nonexistent/file.txt")])


# ── Scenario 5 ──────────────────────────────────────────────────────────────

def test_status_cache_fetch_returns_empty_on_git_unavailable(tmp_path):
    from biome_fm.git.status_cache import GitStatusCache

    cache = GitStatusCache()
    # patch subprocess.run so run_git(safe=True) returns "" → _parse("") → empty
    with patch("subprocess.run", side_effect=FileNotFoundError("no git")):
        status = cache._fetch(tmp_path)
    assert status.statuses == {}
    assert status.dirty_dirs == frozenset()
