"""Tests for git branch operations."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.git.branch_ops import current_branch, list_branches, switch_branch


def _run(stdout: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


REPO = Path("/fake/repo")


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_list_branches_parses_output(mock_run: MagicMock) -> None:
    mock_run.return_value = _run("* main\n  develop\n  feature/foo\n")
    result = list_branches(REPO)
    assert result == ["main", "develop", "feature/foo"]
    mock_run.assert_called_once_with(
        ["git", "branch", "--list"],
        cwd=REPO, capture_output=True, text=True, timeout=5,
    )


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_current_branch_identified(mock_run: MagicMock) -> None:
    mock_run.return_value = _run("main\n")
    assert current_branch(REPO) == "main"


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_detached_head_handled(mock_run: MagicMock) -> None:
    mock_run.return_value = _run("HEAD\n")
    assert current_branch(REPO) == "(detached)"


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_switch_branch_calls_git(mock_run: MagicMock) -> None:
    mock_run.return_value = _run(returncode=0)
    switch_branch(REPO, "develop")
    mock_run.assert_called_once_with(
        ["git", "switch", "develop"],
        cwd=REPO, capture_output=True, text=True, timeout=10,
    )


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_switch_branch_dirty_raises(mock_run: MagicMock) -> None:
    mock_run.return_value = _run(returncode=1, stderr="error: Your local changes would be overwritten")
    with pytest.raises(RuntimeError, match="overwritten"):
        switch_branch(REPO, "develop")


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_not_a_git_repo_returns_empty(mock_run: MagicMock) -> None:
    mock_run.side_effect = FileNotFoundError
    assert list_branches(REPO) == []
    assert current_branch(REPO) == ""


@patch("biome_fm.git.branch_ops.subprocess.run")
def test_switch_branch_no_git_raises_runtime_error(mock_run: MagicMock) -> None:
    mock_run.side_effect = FileNotFoundError("git not found")
    with pytest.raises(RuntimeError):
        switch_branch(REPO, "main")
