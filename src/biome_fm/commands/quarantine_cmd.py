"""Command to remove macOS quarantine xattr."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command


class RemoveQuarantineCmd(Command):
    def __init__(self, paths: list[Path]) -> None:
        self._paths = paths

    def execute(self) -> None:
        from biome_fm.models.finder_tags import _QUARANTINE_ATTR, _getxattr, remove_quarantine_flag
        attr = _QUARANTINE_ATTR.decode()
        for p in self._paths:
            try:
                _getxattr(str(p), attr)
                remove_quarantine_flag(p)
            except OSError:
                pass

    @property
    def description(self) -> str:
        return f"Remove quarantine from {len(self._paths)} file(s)"
