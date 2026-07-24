"""Unit tests for git.branch_ops — no Qt required."""
import os
import subprocess

import pytest

from biome_fm.git.branch_ops import current_branch, list_branches, switch_branch


def test_list_branches_non_repo(tmp_path):
    assert list_branches(tmp_path) == []


def test_current_branch_non_repo(tmp_path):
    assert current_branch(tmp_path) == ""


def test_switch_branch_bad_name(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={**{k: v for k, v in os.environ.items() if k in ("PATH", "HOME")},
             "HOME": str(tmp_path), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    with pytest.raises(RuntimeError):
        switch_branch(tmp_path, "nonexistent-branch-xyz")
