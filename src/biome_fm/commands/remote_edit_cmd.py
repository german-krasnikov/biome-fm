"""RemoteEditCmd — download remote file, open editor, re-upload if changed (F258)."""
from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from biome_fm.commands.base import Command


class RemoteEditCmd(Command):
    """Download → editor → re-upload on mtime change. Not undoable."""

    undoable = False

    def __init__(self, path: Path, vfs, editor_cmd: str) -> None:
        self._path = path
        self._vfs = vfs
        self._editor_cmd = editor_cmd

    def execute(self) -> None:
        data = self._vfs.read_bytes(self._path)
        suffix = self._path.suffix or ".tmp"
        fd, tmp = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, data)
            os.close(fd)
            mtime_before = os.path.getmtime(tmp)
            subprocess.run([*shlex.split(self._editor_cmd), tmp], check=True)
            if os.path.getmtime(tmp) != mtime_before:
                with open(tmp, "rb") as f:
                    self._vfs.write_bytes(self._path, f.read())
        finally:
            Path(tmp).unlink(missing_ok=True)

    def undo(self) -> None:
        pass  # not undoable
