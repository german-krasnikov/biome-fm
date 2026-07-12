"""VFS Router — transparent dispatch by path type."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS

if TYPE_CHECKING:
    from biome_fm.plugins.manager import PluginManager

_BUILTIN_EXTENSIONS: frozenset[str] = frozenset({"zip", "tar", "tar.gz", "tar.bz2", "tar.xz"})


class VFSRouter:
    """Selects VFS by path. Drop-in replacement for LocalVFS."""

    def __init__(self, plugin_manager: PluginManager | None = None) -> None:
        self._local = LocalVFS()
        self._cache: dict[Path, ArchiveVFS] = {}
        self._pm = plugin_manager

    def _archive_extensions(self) -> frozenset[str]:
        exts = set(_BUILTIN_EXTENSIONS)
        if self._pm is not None:
            for lst in self._pm.hook.extra_archive_extensions():
                exts.update(lst)
        return frozenset(exts)

    def _resolve(self, path: Path) -> tuple[LocalVFS | ArchiveVFS, Path]:
        root = _find_archive_root(path, self._archive_extensions())
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


def _find_archive_root(path: Path, extensions: frozenset[str]) -> Path | None:
    """Walk ancestry to find first existing archive file."""
    for p in [path, *path.parents]:
        if p.is_file():
            # Compound suffix first (e.g. "tar.gz"), then single (e.g. "zip")
            if "".join(p.suffixes).lstrip(".") in extensions:
                return p
            if p.suffix.lstrip(".") in extensions:
                return p
    return None
