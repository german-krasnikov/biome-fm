"""Shared git helpers for preview providers."""
from __future__ import annotations

from pathlib import Path

from biome_fm.git.run import run_git  # noqa: F401


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
