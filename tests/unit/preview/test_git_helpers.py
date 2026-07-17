"""Unit tests for _git_helpers — TDD red phase."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_find_repo_finds_git_dir(tmp_path):
    (tmp_path / ".git").mkdir()
    subdir = tmp_path / "a" / "b"
    subdir.mkdir(parents=True)
    from biome_fm.preview.providers._git_helpers import find_repo
    assert find_repo(subdir / "file.py") == tmp_path


def test_find_repo_returns_none_outside_git(tmp_path):
    from biome_fm.preview.providers._git_helpers import find_repo
    assert find_repo(tmp_path / "file.py") is None


def test_run_git_success(tmp_path):
    from biome_fm.preview.providers._git_helpers import run_git
    fake = MagicMock(stdout="hello\n", returncode=0)
    with patch("biome_fm.preview.providers._git_helpers.subprocess.run", return_value=fake):
        assert run_git(["log", "--oneline"], tmp_path) == "hello\n"


def test_run_git_raises_on_nonzero(tmp_path):
    from biome_fm.preview.providers._git_helpers import run_git
    import subprocess
    with patch(
        "biome_fm.preview.providers._git_helpers.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            run_git(["bad"], tmp_path)
