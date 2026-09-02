"""Batch rename command."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class MultiRenameCmd(Command):
    """Rename N files atomically."""

    def __init__(self, renames: list[tuple[Path, Path]], vfs: VFSProtocol) -> None:
        self._renames = renames
        self._vfs = vfs

    def execute(self) -> None:
        for old, new in self._renames:
            self._vfs.move(old, new)

    @property
    def description(self) -> str:
        return f"Rename {len(self._renames)} item(s)"
