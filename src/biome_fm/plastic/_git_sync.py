"""Git Sync backend — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from ._cm import run_cm


def sync_git(url: str, cwd: Path) -> str:
    return run_cm(["sync", "git", url], cwd=cwd, safe=True, timeout=300)


def git_sync_status(cwd: Path) -> str:
    return run_cm(["sync", "git", "--status"], cwd=cwd, safe=True)
