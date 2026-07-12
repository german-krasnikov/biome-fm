"""Move command — move to dest dir (undoable via move back)."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.vfs import VFSProtocol
from biome_fm.operations.task import Cancelled


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


class ProgressMoveCmd(Command):
    """Move with progress reporting and cancel support."""

    def __init__(
        self,
        sources: list[Path],
        dest_dir: Path,
        vfs: VFSProtocol,
        cancel: object,  # threading.Event
        report: Callable[..., None],
    ) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._cancel = cancel
        self._report = report
        self._moves: list[tuple[Path, Path]] = []

    def execute(self) -> None:
        self._moves.clear()
        total = len(self._sources)
        for i, src in enumerate(self._sources):
            if self._cancel.is_set():
                raise Cancelled()
            dst = self._dest_dir / src.name
            self._vfs.move(src, dst)
            self._moves.append((src, dst))
            self._report(i + 1, total, 0, 0, src.name)

    def undo(self) -> None:
        for orig, dst in reversed(self._moves):
            self._vfs.move(dst, orig)
        self._moves.clear()

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Move {n} item{'s' if n != 1 else ''}"
