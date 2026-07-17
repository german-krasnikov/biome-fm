"""Archive creation and extraction commands."""
from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from biome_fm.commands.base import Command


class ArchiveCmd(Command):
    """Create zip archive from sources. Undo = delete archive."""

    undoable = True

    def __init__(self, sources: list[Path], archive_path: Path, fmt: str = "zip") -> None:
        self._sources = sources
        self._archive_path = archive_path
        self._fmt = fmt

    def execute(self) -> None:
        try:
            if self._fmt in ("tar.gz", "tar.bz2"):
                mode = "w:gz" if self._fmt == "tar.gz" else "w:bz2"
                with tarfile.open(self._archive_path, mode) as tf:
                    for src in self._sources:
                        tf.add(src, arcname=src.name)
            else:
                with zipfile.ZipFile(self._archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for src in self._sources:
                        if src.is_dir():
                            for f in src.rglob("*"):
                                if f.is_file():
                                    zf.write(f, f.relative_to(src.parent))
                        else:
                            zf.write(src, src.name)
        except (zipfile.BadZipFile, tarfile.TarError, OSError, PermissionError) as e:
            self._archive_path.unlink(missing_ok=True)
            raise RuntimeError(f"Archive creation failed: {e}") from e

    def undo(self) -> None:
        self._archive_path.unlink(missing_ok=True)

    @property
    def description(self) -> str:
        return f"Archive {len(self._sources)} item(s)"


_ZIP_EXTS = frozenset((".zip", ".jar", ".whl"))


class ExtractCmd(Command):
    """Extract archive to dest_dir. Not undoable."""

    undoable = False

    def __init__(self, archive: Path, dest_dir: Path) -> None:
        self._archive = archive
        self._dest_dir = dest_dir

    def execute(self) -> None:
        try:
            name = self._archive.name.lower()
            if any(name.endswith(e) for e in _ZIP_EXTS):
                with zipfile.ZipFile(self._archive) as zf:
                    zf.extractall(self._dest_dir)
            else:
                with tarfile.open(self._archive) as tf:
                    tf.extractall(self._dest_dir, filter="data")
        except (zipfile.BadZipFile, tarfile.TarError, OSError, PermissionError) as e:
            raise RuntimeError(f"Extraction failed: {e}") from e

    def undo(self) -> None:
        pass
