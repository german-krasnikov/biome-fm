"""Mkdir command — create directory (undoable)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class MkdirCmd(Command):
    def __init__(self, path: Path, vfs: VFSProtocol) -> None:
        if "/" in path.name or "\\" in path.name:
            raise ValueError(f"Invalid directory name: {path.name!r}")
        self._path = path
        self._vfs = vfs

    def execute(self) -> None:
        self._vfs.mkdir(self._path)

    def undo(self) -> None:
        self._vfs.delete(self._path)

    @property
    def description(self) -> str:
        return f"Create folder '{self._path.name}'"
