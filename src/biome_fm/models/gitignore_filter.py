"""GitignoreFilter — checks whether a path is git-ignored."""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitignoreFilter:
    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root
        self._has_git = (repo_root / ".git").exists()

    def is_ignored(self, path: Path) -> bool:
        if not self._has_git:
            return False
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-q", str(path)],
                cwd=self._root,
                capture_output=True,
            )
            return result.returncode == 0
        except OSError:
            return False
