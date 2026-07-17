"""Unit tests for GitignoreFilter."""
import subprocess
from pathlib import Path

import pytest

from biome_fm.models.gitignore_filter import GitignoreFilter


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path, capture_output=True,
    )


def test_ignored_file(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    pyc = tmp_path / "test.pyc"
    pyc.touch()
    assert GitignoreFilter(tmp_path).is_ignored(pyc)


def test_tracked_file_not_ignored(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    py = tmp_path / "main.py"
    py.touch()
    assert not GitignoreFilter(tmp_path).is_ignored(py)


def test_no_git_returns_false(tmp_path: Path) -> None:
    f = GitignoreFilter(tmp_path)
    assert not f.is_ignored(tmp_path / "anything.txt")
