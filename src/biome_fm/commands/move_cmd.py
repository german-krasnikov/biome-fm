"""Move command — move to dest dir."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.conflict_resolver import ConflictAction, ConflictResolver, auto_rename
from biome_fm.models.vfs import VFSProtocol
from biome_fm.operations.task import Cancelled


class MoveCmd(Command):
    def __init__(self, sources: list[Path], dest_dir: Path, vfs: VFSProtocol) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs

    def execute(self) -> None:
        for src in self._sources:
            dst = self._dest_dir / src.name
            self._vfs.move(src, dst)

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Move {n} item{'s' if n != 1 else ''}"

    def preview(self) -> list[str]:
        return [f"Move {s.name}  →  {self._dest_dir / s.name}" for s in self._sources]


class ProgressMoveCmd(Command):
    """Move with progress reporting and cancel support."""

    def __init__(
        self,
        sources: list[Path],
        dest_dir: Path,
        vfs: VFSProtocol,
        cancel: object,  # threading.Event
        report: Callable[..., None],
        conflict_resolver: ConflictResolver | None = None,
    ) -> None:
        self._sources = sources
        self._dest_dir = dest_dir
        self._vfs = vfs
        self._cancel = cancel
        self._report = report
        self._resolver = conflict_resolver

    def execute(self) -> None:
        total = len(self._sources)
        for i, src in enumerate(self._sources):
            if self._cancel.is_set():
                raise Cancelled()
            dst = self._dest_dir / src.name
            overwrite = False
            if dst.exists() and self._resolver is not None:
                action = self._resolver.ask(src, dst)
                if action in (ConflictAction.SKIP, ConflictAction.SKIP_ALL):
                    continue
                if action == ConflictAction.CANCEL:
                    raise Cancelled()
                if action == ConflictAction.RENAME:
                    dst = auto_rename(dst)
                elif action in (ConflictAction.OVERWRITE, ConflictAction.OVERWRITE_ALL):
                    overwrite = True
            if overwrite:
                self._vfs.delete(dst)
            self._vfs.move(src, dst)
            self._report(i + 1, total, 0, 0, src.name)

    @property
    def description(self) -> str:
        n = len(self._sources)
        return f"Move {n} item{'s' if n != 1 else ''}"
