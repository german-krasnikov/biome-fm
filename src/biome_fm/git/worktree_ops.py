"""F293 — Git worktree navigator."""
from __future__ import annotations

import subprocess
from pathlib import Path

_TIMEOUT = 5


def list_worktrees(repo: Path) -> list[dict]:
    """Return list of dicts with keys: path, branch, head."""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return _parse(r.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []


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
