"""Delete command — non-undoable."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class DeleteCmd(Command):
    undoable = False

    def __init__(self, paths: list[Path], vfs: VFSProtocol) -> None:
        self._paths = paths
        self._vfs = vfs

    def execute(self) -> None:
        for p in self._paths:
            self._vfs.delete(p)

    def undo(self) -> None:
        pass  # non-undoable

    @property
    def description(self) -> str:
        n = len(self._paths)
        return f"Delete {n} item{'s' if n != 1 else ''}"
