"""TrashCmd — move files to OS trash (non-undoable)."""
from __future__ import annotations

import warnings
from pathlib import Path

from biome_fm.commands.base import Command

try:
    from send2trash import send2trash as _send2trash
except ImportError:  # pragma: no cover
    def _send2trash(path: str) -> None:  # type: ignore[misc]
        warnings.warn(f"send2trash unavailable; permanently deleting {path}", stacklevel=2)
        Path(path).unlink(missing_ok=True)


class TrashCmd(Command):
    undoable = False

    def __init__(self, paths: list[Path]) -> None:
        self._paths = paths

    def execute(self) -> None:
        for p in self._paths:
            _send2trash(str(p))

    def undo(self) -> None:
        pass  # trash restore not supported by send2trash API

    @property
    def description(self) -> str:
        n = len(self._paths)
        return f"Trash {n} item{'s' if n != 1 else ''}"
