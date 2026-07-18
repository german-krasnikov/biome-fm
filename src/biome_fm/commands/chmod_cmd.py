"""Batch chmod command with undo (F210, POSIX only)."""
from __future__ import annotations

import os
from pathlib import Path

from biome_fm.commands.base import Command


class ChmodCmd(Command):
    def __init__(
        self,
        paths: list[Path],
        mode: int,
        recursive: bool = False,
        vfs=None,
    ) -> None:
        self._paths = list(paths)
        self._mode = mode
        self._recursive = recursive
        self._vfs = vfs
        self._saved: dict[Path, int] = {}

    def execute(self) -> None:
        if self._vfs is not None and hasattr(self._vfs, "chmod"):
            for p in self._paths:
                self._vfs.chmod(p, self._mode)
            return
        self._saved.clear()
        for p in self._paths:
            self._apply(p)

    def _apply(self, p: Path) -> None:
        try:
            self._saved[p] = p.stat().st_mode & 0o777
            os.chmod(p, self._mode)
            if self._recursive and p.is_dir():
                for child in p.rglob("*"):
                    self._saved[child] = child.stat().st_mode & 0o777
                    os.chmod(child, self._mode)
        except OSError:
            pass

    def undo(self) -> None:
        for p, mode in reversed(list(self._saved.items())):
            try:
                os.chmod(p, mode)
            except OSError:
                pass

    @property
    def description(self) -> str:
        return f"chmod {oct(self._mode)} on {len(self._paths)} item(s)"
