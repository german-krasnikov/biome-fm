"""Rename command — rename in place (undoable)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class RenameCmd(Command):
    def __init__(self, src: Path, new_name: str, vfs: VFSProtocol) -> None:
        if "/" in new_name or "\\" in new_name:
            raise ValueError(f"Name contains path separator: {new_name!r}")
        self._src = src
        self._dst = src.parent / new_name
        self._vfs = vfs

    def execute(self) -> None:
        self._vfs.move(self._src, self._dst)

    def undo(self) -> None:
        self._vfs.move(self._dst, self._src)

    @property
    def description(self) -> str:
        return f"Rename '{self._src.name}' → '{self._dst.name}'"
