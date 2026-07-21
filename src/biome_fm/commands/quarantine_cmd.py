"""Command to remove macOS quarantine xattr with undo support."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command


class RemoveQuarantineCmd(Command):
    undoable = True

    def __init__(self, paths: list[Path]) -> None:
        self._paths = paths
        self._removed: list[tuple[Path, bytes]] = []

    def execute(self) -> None:
        from biome_fm.models.finder_tags import _getxattr, _QUARANTINE_ATTR, remove_quarantine_flag
        attr = _QUARANTINE_ATTR.decode()
        self._removed = []
        for p in self._paths:
            try:
                old = _getxattr(str(p), attr)
                remove_quarantine_flag(p)
                self._removed.append((p, old))
            except OSError:
                pass

    def undo(self) -> None:
        from biome_fm.models.finder_tags import _setxattr, _QUARANTINE_ATTR
        attr = _QUARANTINE_ATTR.decode()
        for p, val in self._removed:
            try:
                _setxattr(str(p), attr, val)
            except OSError:
                pass

    @property
    def description(self) -> str:
        return f"Remove quarantine from {len(self._paths)} file(s)"
