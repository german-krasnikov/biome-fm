"""Shared git helpers for preview providers."""
from __future__ import annotations

import subprocess
from pathlib import Path


def find_repo(path: Path) -> Path | None:
    """Walk up from path looking for .git directory."""
    cur = path.parent.resolve()
    while True:
        if (cur / ".git").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def run_git(args: list[str], cwd: Path, timeout: int = 5) -> str:
    """Run git command, return stdout. Raise on error."""
    r = subprocess.run(
        ["git"] + args, cwd=cwd,
        capture_output=True, text=True, timeout=timeout, check=True,
    )
    return r.stdout
