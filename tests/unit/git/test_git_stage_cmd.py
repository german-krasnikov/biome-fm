from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

from biome_fm.commands.git_stage import GitStageCmd, GitUnstageCmd


def test_stage_is_undoable():
    cmd = GitStageCmd(Path("/repo/a.py"), Path("/repo"))
    assert cmd.undoable is True


def test_unstage_is_undoable():
    cmd = GitUnstageCmd(Path("/repo/a.py"), Path("/repo"))
    assert cmd.undoable is True


def test_stage_calls_git_add():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitStageCmd(p, repo)
    with patch("subprocess.run") as mock_run:
        cmd.execute()
    mock_run.assert_called_once_with(
        ["git", "add", str(p)], cwd=repo, check=True, timeout=10
    )


def test_stage_undo_calls_restore_staged():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitStageCmd(p, repo)
    with patch("subprocess.run") as mock_run:
        cmd.undo()
    mock_run.assert_called_once_with(
        ["git", "restore", "--staged", str(p)], cwd=repo, check=True, timeout=10
    )


def test_unstage_calls_restore_staged():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitUnstageCmd(p, repo)
    with patch("subprocess.run") as mock_run:
        cmd.execute()
    mock_run.assert_called_once_with(
        ["git", "restore", "--staged", str(p)], cwd=repo, check=True, timeout=10
    )


def test_unstage_undo_calls_git_add():
    p, repo = Path("/repo/a.py"), Path("/repo")
    cmd = GitUnstageCmd(p, repo)
    with patch("subprocess.run") as mock_run:
        cmd.undo()
    mock_run.assert_called_once_with(
        ["git", "add", str(p)], cwd=repo, check=True, timeout=10
    )
