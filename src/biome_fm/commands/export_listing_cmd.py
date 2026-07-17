"""Export directory listing to txt or csv."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.file_item import FileItem


class ExportListingCmd(Command):
    undoable = False

    def __init__(self, items: list[FileItem], dest: Path, fmt: str = "txt") -> None:
        self._items = items
        self._dest = dest
        self._fmt = fmt

    def execute(self) -> None:
        if self._fmt == "csv":
            self._write_csv()
        else:
            self._write_txt()

    def _write_txt(self) -> None:
        lines = [
            f"{item.name}\t{item.size}\t{datetime.fromtimestamp(item.modified).isoformat()}"
            for item in self._items
        ]
        self._dest.write_text("\n".join(lines))

    def _write_csv(self) -> None:
        with self._dest.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["name", "size", "modified"])
            for item in self._items:
                w.writerow([item.name, item.size, datetime.fromtimestamp(item.modified).isoformat()])

    def undo(self) -> None:
        pass
