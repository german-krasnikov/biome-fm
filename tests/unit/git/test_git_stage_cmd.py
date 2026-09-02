from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.commands.git_stage import GitStageCmd, GitUnstageCmd


def _mock_run():
    m = MagicMock()
    m.stdout = ""
    return m


def test_stage_calls_git_add():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitStageCmd(p, repo)
    with patch("biome_fm.git.run.subprocess.run", return_value=_mock_run()) as mock_run:
        cmd.execute()
    mock_run.assert_called_once_with(
        ["git", "add", str(p)], cwd=repo,
        capture_output=True, text=True, timeout=10, check=True,
    )


def test_stage_execute_calls_git_add():
    """Regression guard: execute() still calls git add after undo removal."""
    p, repo = Path("/repo/b.py"), Path("/repo")
    cmd = GitStageCmd(p, repo)
    with patch("biome_fm.git.run.subprocess.run", return_value=_mock_run()) as mock_run:
        cmd.execute()
    mock_run.assert_called_once_with(
        ["git", "add", str(p)], cwd=repo,
        capture_output=True, text=True, timeout=10, check=True,
    )


def test_unstage_calls_restore_staged():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitUnstageCmd(p, repo)
    with patch("biome_fm.git.run.subprocess.run", return_value=_mock_run()) as mock_run:
        cmd.execute()
    mock_run.assert_called_once_with(
        ["git", "restore", "--staged", str(p)], cwd=repo,
        capture_output=True, text=True, timeout=10, check=True,
    )
