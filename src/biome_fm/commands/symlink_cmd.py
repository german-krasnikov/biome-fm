"""Symlink and hardlink creation commands."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.commands.base import Command


class SymlinkCmd(Command):
    """Create a symbolic link."""

    def __init__(self, target: Path, link: Path) -> None:
        self._target = target
        self._link = link

    def execute(self) -> None:
        self._link.symlink_to(self._target)

    @property
    def description(self) -> str:
        return f"Symlink '{self._link.name}' → '{self._target.name}'"


class HardlinkCmd(Command):
    """Create a hard link."""

    def __init__(self, target: Path, link: Path) -> None:
        self._target = target
        self._link = link

    def execute(self) -> None:
        os.link(self._target, self._link)

    @property
    def description(self) -> str:
        return f"Hardlink '{self._link.name}' → '{self._target.name}'"
