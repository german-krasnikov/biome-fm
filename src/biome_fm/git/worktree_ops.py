"""F293 — Git worktree navigator."""
from __future__ import annotations

from pathlib import Path

from biome_fm.git.run import run_git


def list_worktrees(repo: Path) -> list[dict]:
    """Return list of dicts with keys: path, branch, head."""
    raw = run_git(["worktree", "list", "--porcelain"], cwd=repo, timeout=5, safe=True)
    return _parse(raw) if raw else []


def _parse(output: str) -> list[dict]:
    result: list[dict] = []
    current: dict = {}
    for line in output.splitlines():
        if line.startswith("worktree "):
            if current:
                result.append(current)
            current = {"path": Path(line[9:]), "head": "", "branch": ""}
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch refs/heads/"):
            current["branch"] = line[len("branch refs/heads/"):]
    if current:
        result.append(current)
    return result
