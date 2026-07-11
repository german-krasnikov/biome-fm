"""VFS Router — transparent dispatch by path type."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS


class VFSRouter:
    """Selects VFS by path. Drop-in replacement for LocalVFS."""

    def __init__(self) -> None:
        self._local = LocalVFS()
        self._cache: dict[Path, ArchiveVFS] = {}

    def _resolve(self, path: Path) -> tuple[LocalVFS | ArchiveVFS, Path]:
        root = _find_archive_root(path)
        if root is None:
            return self._local, path
        if root not in self._cache:
            self._cache[root] = ArchiveVFS(root)
        return self._cache[root], path

    def listdir(self, path: Path) -> list[FileItem]:
        vfs, p = self._resolve(path)
        return vfs.listdir(p)

    def stat(self, path: Path) -> FileItem:
        vfs, p = self._resolve(path)
        return vfs.stat(p)

    def exists(self, path: Path) -> bool:
        vfs, p = self._resolve(path)
        return vfs.exists(p)

    def copy(self, src: Path, dst: Path) -> None:
        vfs, _ = self._resolve(src)
        vfs.copy(src, dst)

    def move(self, src: Path, dst: Path) -> None:
        vfs, _ = self._resolve(src)
        vfs.move(src, dst)

    def delete(self, path: Path) -> None:
        vfs, p = self._resolve(path)
        vfs.delete(p)

    def mkdir(self, path: Path) -> None:
        vfs, p = self._resolve(path)
        vfs.mkdir(p)


def _find_archive_root(path: Path) -> Path | None:
    """Walk ancestry to find first existing archive file."""
    for p in [path, *path.parents]:
        if p.is_file():
            s = p.suffixes
            if s[-1:] == [".zip"] or s[-1:] == [".tar"] or s[-2:] == [".tar", ".gz"]:
                return p
    return None
