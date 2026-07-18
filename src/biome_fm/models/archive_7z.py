"""Read-only VFS for .7z (py7zr) and .rar (rarfile) archives."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.archive_vfs import _child_of
from biome_fm.models.file_item import FileItem


class SevenZipVFS:
    """Browse .7z archives. Requires: pip install py7zr"""

    def __init__(self, archive_path: Path) -> None:
        try:
            import py7zr
        except ImportError:
            raise ImportError("pip install py7zr for .7z support")
        self._path = archive_path
        self._py7zr = py7zr

    def listdir(self, path: Path) -> list[FileItem]:
        prefix = self._internal_path(path)
        seen: set[str] = set()
        items: list[FileItem] = []
        with self._py7zr.SevenZipFile(self._path, "r") as z:
            for info in z.list():
                result = _child_of(info.filename, prefix)
                if result is None or result[0] in seen:
                    continue
                child, is_nested = result
                seen.add(child)
                is_dir = is_nested or info.is_directory
                vpath = self._path / (f"{prefix}/{child}" if prefix else child)
                size = 0 if is_dir else (info.uncompressed or 0)
                ts = info.creationtime.timestamp() if info.creationtime else 0.0
                items.append(FileItem(name=child, path=vpath, is_dir=is_dir, size=size, modified=ts))
        return items

    def read_bytes(self, path: Path) -> bytes:
        internal = self._internal_path(path)
        with self._py7zr.SevenZipFile(self._path, "r") as z:
            result = z.read([internal])
            bio = result.get(internal)
            return bio.read() if bio is not None else b""

    def _internal_path(self, path: Path) -> str:
        if path == self._path:
            return ""
        return "/".join(path.relative_to(self._path).parts)


class RarVFS:
    """Browse .rar archives. Requires: pip install rarfile"""

    def __init__(self, archive_path: Path) -> None:
        try:
            import rarfile
        except ImportError:
            raise ImportError("pip install rarfile for .rar support")
        self._path = archive_path
        self._rarfile = rarfile

    def listdir(self, path: Path) -> list[FileItem]:
        prefix = self._internal_path(path)
        seen: set[str] = set()
        items: list[FileItem] = []
        with self._rarfile.RarFile(self._path) as rf:
            for info in rf.infolist():
                result = _child_of(info.filename, prefix)
                if result is None or result[0] in seen:
                    continue
                child, is_nested = result
                seen.add(child)
                is_dir = is_nested or info.is_dir()
                vpath = self._path / (f"{prefix}/{child}" if prefix else child)
                size = 0 if is_dir else info.file_size
                ts = info.mtime.timestamp() if info.mtime else 0.0
                items.append(FileItem(name=child, path=vpath, is_dir=is_dir, size=size, modified=ts))
        return items

    def read_bytes(self, path: Path) -> bytes:
        internal = self._internal_path(path)
        with self._rarfile.RarFile(self._path) as rf:
            return rf.read(internal)

    def _internal_path(self, path: Path) -> str:
        if path == self._path:
            return ""
        return "/".join(path.relative_to(self._path).parts)
