"""Pure-Python git branch operations — no Qt."""
from __future__ import annotations

import subprocess
from pathlib import Path

_TIMEOUT = 5


def list_branches(repo: Path) -> list[str]:
    """Return all local branches. Empty list if not a git repo."""
    try:
        r = subprocess.run(
            ["git", "branch", "--list"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return [line.lstrip("* ").strip() for line in r.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []


def current_branch(repo: Path) -> str:
    """Return current branch name, '(detached)' on detached HEAD, '' on error."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        name = r.stdout.strip()
        return "(detached)" if name == "HEAD" else name
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def switch_branch(repo: Path, branch: str) -> None:
    """Switch to branch. Raises RuntimeError on failure (dirty tree, etc.)."""
    try:
        r = subprocess.run(
            ["git", "switch", branch],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError(str(exc)) from exc
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git switch {branch} failed")
