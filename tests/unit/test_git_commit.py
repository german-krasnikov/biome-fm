"""Unit tests for git commit operations."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from biome_fm.git.commit_ops import commit, stage_files, staged_files, unstage_files

REPO = Path("/fake/repo")


def _run(stdout="", returncode=0):
    r = MagicMock()
    r.stdout = stdout
    r.returncode = returncode
    r.stderr = ""
    return r


# --- stage ---

def test_stage_files_calls_git_add():
    with patch("biome_fm.git.commit_ops.subprocess.run", return_value=_run()) as mock:
        stage_files(REPO, [Path("a.txt"), Path("b.txt")])
    mock.assert_called_once_with(
        ["git", "add", "--", "a.txt", "b.txt"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )


# --- unstage ---

def test_unstage_files_calls_git_reset():
    with patch("biome_fm.git.commit_ops.subprocess.run", return_value=_run()) as mock:
        unstage_files(REPO, [Path("a.txt")])
    mock.assert_called_once_with(
        ["git", "reset", "HEAD", "--", "a.txt"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )


# --- staged_files ---

def test_staged_files_parses_status():
    with patch("biome_fm.git.commit_ops.subprocess.run", return_value=_run("a.txt\nb.txt\n")):
        result = staged_files(REPO)
    assert result == ["a.txt", "b.txt"]


def test_staged_files_empty():
    with patch("biome_fm.git.commit_ops.subprocess.run", return_value=_run("")):
        assert staged_files(REPO) == []


# --- commit ---

def test_commit_calls_git_commit():
    responses = [_run(), _run("abc1234\n")]  # commit, then rev-parse
    with patch("biome_fm.git.commit_ops.subprocess.run", side_effect=responses) as mock:
        hash_ = commit(REPO, "feat: add thing")
    assert hash_ == "abc1234"
    assert mock.call_count == 2
    first_call = mock.call_args_list[0]
    assert first_call == call(
        ["git", "commit", "-m", "feat: add thing"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )


def test_commit_empty_message_raises():
    with pytest.raises(ValueError, match="message"):
        commit(REPO, "")


def test_commit_nothing_staged_raises():
    r = _run("nothing to commit", returncode=1)
    r.stderr = "nothing to commit"
    with patch("biome_fm.git.commit_ops.subprocess.run", return_value=r):
        with pytest.raises(RuntimeError, match="nothing to commit"):
            commit(REPO, "fix: something")
