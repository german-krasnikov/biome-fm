"""Archive creation and extraction commands."""
from __future__ import annotations

import shutil
import subprocess
import tarfile
import threading
import zipfile
from collections.abc import Callable
from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.operations.task import Cancelled


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


_VALID_FMTS = frozenset({"zip", "tar.gz", "tar.bz2"})


class ProgressArchiveCmd(Command):
    """Archive with cancel + per-file progress callback."""

    undoable = True

    def __init__(
        self,
        sources: list[Path],
        archive_path: Path,
        fmt: str,
        cancel: threading.Event,
        progress: Callable[..., None],
    ) -> None:
        self._sources = sources
        self._archive_path = archive_path
        self._fmt = fmt
        self._cancel = cancel
        self._progress = progress

    def execute(self) -> None:
        if self._fmt not in _VALID_FMTS:
            raise ValueError(f"Unknown archive format: {self._fmt!r}")
        files = self._collect_files()
        try:
            if self._fmt in ("tar.gz", "tar.bz2"):
                mode = "w:gz" if self._fmt == "tar.gz" else "w:bz2"
                with tarfile.open(self._archive_path, mode) as tf:
                    for i, (src, arcname) in enumerate(files):
                        if self._cancel.is_set():
                            raise Cancelled()
                        tf.add(src, arcname=arcname)
                        self._progress(i + 1, len(files), 0, 0, src.name)
            else:
                with zipfile.ZipFile(self._archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, (src, arcname) in enumerate(files):
                        if self._cancel.is_set():
                            raise Cancelled()
                        zf.write(src, arcname)
                        self._progress(i + 1, len(files), 0, 0, src.name)
        except Cancelled:
            self._archive_path.unlink(missing_ok=True)
            raise

    def _collect_files(self) -> list[tuple[Path, str]]:
        files: list[tuple[Path, str]] = []
        for src in self._sources:
            if src.is_dir():
                for f in src.rglob("*"):
                    if self._cancel.is_set():
                        raise Cancelled()
                    if f.is_file():
                        files.append((f, str(f.relative_to(src.parent))))
            else:
                files.append((src, src.name))
        return files

    def undo(self) -> None:
        self._archive_path.unlink(missing_ok=True)

    @property
    def description(self) -> str:
        return f"Archive {len(self._sources)} item(s)"


class VerifyArchiveCmd(Command):
    """Test archive integrity. Not undoable. execute() returns '' on success, error on failure."""

    undoable = False

    def __init__(self, archive_path: Path) -> None:
        self._path = archive_path

    def execute(self) -> str:  # type: ignore[override]
        suffix = "".join(self._path.suffixes).lstrip(".")
        try:
            if suffix == "zip":
                with zipfile.ZipFile(self._path) as z:
                    bad = z.testzip()
                    return f"Bad file: {bad}" if bad else ""
            elif suffix in ("tar", "tar.gz", "tar.bz2", "tar.xz", "tgz"):
                with tarfile.open(self._path) as t:
                    for member in t.getmembers():
                        if member.isfile():
                            t.extractfile(member)
                    return ""
            else:
                return f"Unsupported format: {suffix}"
        except (zipfile.BadZipFile, tarfile.TarError, OSError) as e:
            return str(e)

    def undo(self) -> None:
        pass

    @property
    def description(self) -> str:
        return f"Verify {self._path.name}"


class Encrypted7zCmd(Command):
    """Create AES-256 encrypted 7z via system 7z binary."""

    undoable = True

    def __init__(self, sources: list[Path], archive_path: Path, password: str) -> None:
        self._sources = sources
        self._archive_path = archive_path
        self._password = password

    def execute(self) -> None:
        bin7z = shutil.which("7z") or shutil.which("7za")
        if bin7z is None:
            raise RuntimeError("7z binary not found. Install p7zip.")
        cmd = [bin7z, "a", "-p", "-mhe=on",
               str(self._archive_path)] + [str(s) for s in self._sources]
        try:
            result = subprocess.run(
                cmd,
                input=f"{self._password}\n{self._password}\n",
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired:
            self.undo()
            raise RuntimeError("7z timed out after 300 seconds")
        if result.returncode != 0:
            raise RuntimeError(f"7z failed: {result.stderr.strip()}")

    def undo(self) -> None:
        self._archive_path.unlink(missing_ok=True)

    @property
    def description(self) -> str:
        return f"Encrypted archive {self._archive_path.name}"


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
