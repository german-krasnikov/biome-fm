"""Move command — move to dest dir (undoable via move back)."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol


class MoveCmd(Command):
    def __init__(self, sources: list[Path], dest_dir: Path, vfs: VFSProtocol) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._moves: list[tuple[Path, Path]] = []

    def execute(self) -> None:
        self._moves.clear()
        for src in self._sources:
            dst = self._dest_dir / src.name
            self._vfs.move(src, dst)
            self._moves.append((src, dst))

    def undo(self) -> None:
        for orig, dst in reversed(self._moves):
            self._vfs.move(dst, orig)
        self._moves.clear()

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Move {n} item{'s' if n != 1 else ''}"
