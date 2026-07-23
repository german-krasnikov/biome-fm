from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.git.run import run_git


class GitStageCmd(Command):
    undoable = True

    def __init__(self, path: Path, repo_root: Path) -> None:
        self._path = path
        self._repo = repo_root

    def execute(self) -> None:
        run_git(["add", str(self._path)], cwd=self._repo, timeout=10)

    def undo(self) -> None:
        run_git(["restore", "--staged", str(self._path)], cwd=self._repo, timeout=10)


class GitUnstageCmd(Command):
    undoable = True

    def __init__(self, path: Path, repo_root: Path) -> None:
        self._path = path
        self._repo = repo_root

    def execute(self) -> None:
        run_git(["restore", "--staged", str(self._path)], cwd=self._repo, timeout=10)

    def undo(self) -> None:
        run_git(["add", str(self._path)], cwd=self._repo, timeout=10)
