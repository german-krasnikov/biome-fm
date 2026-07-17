"""Bulk rename via $EDITOR — write names to temp file, diff, apply RenameCmd."""
from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.commands.rename_cmd import RenameCmd
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


def _default_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(path)], check=True)


class EditorRenameCmd(Command):
    undoable = True

    def __init__(
        self,
        items: list[FileItem],
        vfs: VFSProtocol,
        editor: Callable[[Path], None] | None = None,
    ) -> None:
        self._items = items
        self._vfs = vfs
        self._editor = editor or _default_editor
        self._sub_cmds: list[RenameCmd] = []

    def execute(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            tmp = Path(f.name)
            f.write("\n".join(item.name for item in self._items) + "\n")
        try:
            self._editor(tmp)
            new_names = tmp.read_text().splitlines()
        finally:
            tmp.unlink(missing_ok=True)

        self._sub_cmds = []
        for item, new_name in zip(self._items, new_names):
            new_name = new_name.strip()
            if new_name and new_name != item.name:
                cmd = RenameCmd(item.path, new_name, self._vfs)
                cmd.execute()
                self._sub_cmds.append(cmd)

    def undo(self) -> None:
        for cmd in reversed(self._sub_cmds):
            cmd.undo()

    @property
    def description(self) -> str:
        return f"Editor rename {len(self._items)} item(s)"
