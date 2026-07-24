"""Tests for git worktree_ops — Item #53."""
from __future__ import annotations

import subprocess



def test_list_worktrees_non_repo(tmp_path):
    from biome_fm.git.worktree_ops import list_worktrees

    assert list_worktrees(tmp_path) == []


def test_parse_porcelain():
    from biome_fm.git.worktree_ops import _parse

    sample = (
        "worktree /home/user/proj\n"
        "HEAD abc1234\n"
        "branch refs/heads/main\n"
        "\n"
        "worktree /home/user/proj-feat\n"
        "HEAD def5678\n"
        "branch refs/heads/feature/foo\n"
    )
    result = _parse(sample)
    assert len(result) == 2
    assert result[0]["branch"] == "main"
    assert result[1]["branch"] == "feature/foo"
    assert result[0]["head"] == "abc1234"


def test_worktree_navigate(tmp_path):
    from biome_fm.git.worktree_ops import list_worktrees

    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={**__import__("os").environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    wt = tmp_path / "wt-branch"
    subprocess.run(
        ["git", "worktree", "add", str(wt), "-b", "wt-branch"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    result = list_worktrees(tmp_path)
    paths = [w["path"] for w in result]
    assert tmp_path in paths
    assert wt in paths
