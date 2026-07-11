"""Copy command — copy to dest dir (undoable via delete)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class CopyCmd(Command):
    def __init__(self, sources: list[Path], dest_dir: Path, vfs: VFSProtocol) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._created: list[Path] = []

    def execute(self) -> None:
        self._created.clear()
        for src in self._sources:
            dst = self._dest_dir / src.name
            self._vfs.copy(src, dst)
            self._created.append(dst)

    def undo(self) -> None:
        for p in reversed(self._created):
            self._vfs.delete(p)
        self._created.clear()

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Copy {n} item{'s' if n != 1 else ''}"
