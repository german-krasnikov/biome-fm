"""Batch chown command with undo (F449, POSIX only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from biome_fm.commands.base import Command


class ChownCmd(Command):
    undoable = True

    def __init__(self, paths: list[Path], uid: int, gid: int) -> None:
        self._paths = list(paths)
        self._uid = uid
        self._gid = gid
        self._old: list[tuple[Path, int, int]] = []

    def execute(self) -> None:
        if sys.platform == "win32":
            raise NotImplementedError("chown is not supported on Windows")
        self._old.clear()
        for p in self._paths:
            st = p.stat()
            self._old.append((p, st.st_uid, st.st_gid))
            os.chown(p, self._uid, self._gid)

    def undo(self) -> None:
        for p, uid, gid in self._old:
            os.chown(p, uid, gid)

    @property
    def description(self) -> str:
        return f"chown {self._uid}:{self._gid} on {len(self._paths)} file(s)"
