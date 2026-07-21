"""Pure-Python git commit operations — no Qt."""
from __future__ import annotations

import subprocess
from pathlib import Path

_TIMEOUT = 10


def stage_files(repo: Path, paths: list[Path]) -> None:
    """Stage files via git add."""
    r = subprocess.run(
        ["git", "add", "--"] + [str(p) for p in paths],
        cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git add failed")


def unstage_files(repo: Path, paths: list[Path]) -> None:
    """Unstage files via git reset HEAD."""
    r = subprocess.run(
        ["git", "reset", "HEAD", "--"] + [str(p) for p in paths],
        cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git reset failed")


def staged_files(repo: Path) -> list[str]:
    """Return list of staged file paths. Empty list if not a git repo."""
    try:
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return [line for line in r.stdout.splitlines() if line]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []


def staged_diff(repo: Path) -> str:
    """Return full staged diff. Empty string if not a git repo or no changes."""
    try:
        r = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def commit(repo: Path, message: str) -> str:
    """Commit staged files. Returns short hash. Raises ValueError/RuntimeError."""
    if not message.strip():
        raise ValueError("commit message cannot be empty")
    r = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "git commit failed")
    rev = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo, capture_output=True, text=True, timeout=_TIMEOUT,
    )
    return rev.stdout.strip()
