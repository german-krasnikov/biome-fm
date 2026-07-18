"""F293 — Git worktree navigator."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.git.worktree_ops import list_worktrees

_PORCELAIN = """\
worktree /repo/main
HEAD abc1234567890123456789012345678901234567890
branch refs/heads/main

worktree /repo/.git/worktrees/feat
HEAD def1234567890123456789012345678901234567890
branch refs/heads/feat/my-feature

"""


def test_parse_worktree_list(monkeypatch):
    import subprocess
    proc = type("P", (), {"stdout": _PORCELAIN, "returncode": 0})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: proc)
    result = list_worktrees(Path("/repo/main"))
    assert len(result) == 2
    assert result[0] == {
        "path": Path("/repo/main"),
        "head": "abc1234567890123456789012345678901234567890",
        "branch": "main",
    }
    assert result[1]["branch"] == "feat/my-feature"
    assert result[1]["path"] == Path("/repo/.git/worktrees/feat")


def test_empty_repo_returns_single_worktree(monkeypatch):
    """A repo with no linked worktrees returns one entry."""
    import subprocess
    single = "worktree /solo\nHEAD aaa\nbranch refs/heads/main\n\n"
    proc = type("P", (), {"stdout": single, "returncode": 0})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: proc)
    result = list_worktrees(Path("/solo"))
    assert len(result) == 1
    assert result[0]["branch"] == "main"
