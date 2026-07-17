"""Symlink and hardlink creation commands."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.commands.base import Command


class SymlinkCmd(Command):
    """Create a symbolic link. Undo = remove the link."""

    undoable = True

    def __init__(self, target: Path, link: Path) -> None:
        self._target = target
        self._link = link

    def execute(self) -> None:
        self._link.symlink_to(self._target)

    def undo(self) -> None:
        self._link.unlink(missing_ok=True)

    @property
    def description(self) -> str:
        return f"Symlink '{self._link.name}' → '{self._target.name}'"


class HardlinkCmd(Command):
    """Create a hard link. Undo = remove the link."""

    undoable = True

    def __init__(self, target: Path, link: Path) -> None:
        self._target = target
        self._link = link

    def execute(self) -> None:
        os.link(self._target, self._link)

    def undo(self) -> None:
        self._link.unlink(missing_ok=True)

    @property
    def description(self) -> str:
        return f"Hardlink '{self._link.name}' → '{self._target.name}'"
