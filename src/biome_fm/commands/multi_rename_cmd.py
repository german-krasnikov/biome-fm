"""Batch rename command — undoable."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class MultiRenameCmd(Command):
    """Rename N files atomically; undo reverses in order."""

    undoable = True

    def __init__(self, renames: list[tuple[Path, Path]], vfs: VFSProtocol) -> None:
        self._renames = renames
        self._vfs = vfs
        self._done: list[tuple[Path, Path]] = []

    def execute(self) -> None:
        self._done = []
        for old, new in self._renames:
            self._vfs.move(old, new)
            self._done.append((old, new))

    def undo(self) -> None:
        for old, new in reversed(self._done):
            self._vfs.move(new, old)

    @property
    def description(self) -> str:
        return f"Rename {len(self._renames)} item(s)"
