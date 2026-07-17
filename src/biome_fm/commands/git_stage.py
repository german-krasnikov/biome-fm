from __future__ import annotations

import subprocess
from pathlib import Path

from biome_fm.commands.base import Command


class GitStageCmd(Command):
    undoable = True

    def __init__(self, path: Path, repo_root: Path) -> None:
        self._path = path
        self._repo = repo_root

    def execute(self) -> None:
        subprocess.run(["git", "add", str(self._path)], cwd=self._repo, check=True, timeout=10)

    def undo(self) -> None:
        subprocess.run(["git", "restore", "--staged", str(self._path)], cwd=self._repo, check=True, timeout=10)


class GitUnstageCmd(Command):
    undoable = True

    def __init__(self, path: Path, repo_root: Path) -> None:
        self._path = path
        self._repo = repo_root

    def execute(self) -> None:
        subprocess.run(["git", "restore", "--staged", str(self._path)], cwd=self._repo, check=True, timeout=10)

    def undo(self) -> None:
        subprocess.run(["git", "add", str(self._path)], cwd=self._repo, check=True, timeout=10)
