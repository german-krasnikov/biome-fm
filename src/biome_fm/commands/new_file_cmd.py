"""NewFileCmd — create a file with optional content."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command


class NewFileCmd(Command):
    """Create a file at path with content."""

    def __init__(self, path: Path, content: bytes = b"") -> None:
        self._path = path
        self._content = content

    def execute(self) -> None:
        self._path.write_bytes(self._content)

    @property
    def description(self) -> str:
        return f"Create file '{self._path.name}'"
