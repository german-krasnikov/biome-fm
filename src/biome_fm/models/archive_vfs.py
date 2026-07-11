"""Read-only VFS for zip and tar.gz archives."""
from __future__ import annotations

import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

from biome_fm.models.file_item import FileItem


class ArchiveVFS:
    """Browse zip/tar.gz archives as directories. Read-only."""

    def __init__(self, archive_path: Path) -> None:
        self._archive = archive_path
        self._is_tar = _is_tar(archive_path)

    def listdir(self, path: Path) -> list[FileItem]:
        prefix = self._internal_path(path)
        return self._list_tar(prefix) if self._is_tar else self._list_zip(prefix)

    def stat(self, path: Path) -> FileItem:
        internal = self._internal_path(path)
        return self._stat_tar(internal) if self._is_tar else self._stat_zip(internal)

    def exists(self, path: Path) -> bool:
        try:
            self.stat(path)
            return True
        except (KeyError, OSError, ValueError):
            return False

    def copy(self, src: Path, dst: Path) -> None:
        raise NotImplementedError("ArchiveVFS is read-only")

    def move(self, src: Path, dst: Path) -> None:
        raise NotImplementedError("ArchiveVFS is read-only")

    def delete(self, path: Path) -> None:
        raise NotImplementedError("ArchiveVFS is read-only")

    def mkdir(self, path: Path) -> None:
        raise NotImplementedError("ArchiveVFS is read-only")

    # ------------------------------------------------------------------
    def _internal_path(self, path: Path) -> str:
        if path == self._archive:
            return ""
        return "/".join(path.relative_to(self._archive).parts)

    def _list_zip(self, prefix: str) -> list[FileItem]:
        seen: set[str] = set()
        items: list[FileItem] = []
        with zipfile.ZipFile(self._archive) as zf:
            for info in zf.infolist():
                raw = info.filename.rstrip("/")
                if not raw or ".." in raw.split("/"):
                    continue
                if prefix:
                    if not raw.startswith(prefix + "/"):
                        continue
                    rel = raw[len(prefix) + 1:]
                else:
                    rel = raw
                if not rel:
                    continue
                child = rel.split("/")[0]
                if child in seen:
                    continue
                seen.add(child)
                parts = rel.split("/")
                is_dir = len(parts) > 1 or info.filename.endswith("/")
                vpath = self._archive / (f"{prefix}/{child}" if prefix else child)
                ts = datetime(*info.date_time).timestamp()
                items.append(FileItem(
                    name=child, path=vpath, is_dir=is_dir,
                    size=0 if is_dir else info.file_size, modified=ts,
                ))
        return items

    def _stat_zip(self, internal: str) -> FileItem:
        with zipfile.ZipFile(self._archive) as zf:
            namelist = zf.namelist()
            if internal in namelist:
                info = zf.getinfo(internal)
                ts = datetime(*info.date_time).timestamp()
                return FileItem(
                    name=Path(internal).name, path=self._archive / internal,
                    is_dir=False, size=info.file_size, modified=ts,
                )
            dir_key = internal + "/"
            if dir_key in namelist:
                info = zf.getinfo(dir_key)
                ts = datetime(*info.date_time).timestamp()
                return FileItem(
                    name=Path(internal).name, path=self._archive / internal,
                    is_dir=True, size=0, modified=ts,
                )
            # Virtual (implicit) directory
            if any(n.startswith(dir_key) for n in namelist):
                return FileItem(
                    name=Path(internal).name, path=self._archive / internal,
                    is_dir=True, size=0, modified=0.0,
                )
        raise KeyError(internal)

    def _list_tar(self, prefix: str) -> list[FileItem]:
        seen: set[str] = set()
        items: list[FileItem] = []
        with tarfile.open(self._archive) as tf:
            for member in tf.getmembers():
                raw = member.name.rstrip("/")
                if not raw or raw == "." or ".." in raw.split("/"):
                    continue
                if prefix:
                    if not raw.startswith(prefix + "/"):
                        continue
                    rel = raw[len(prefix) + 1:]
                else:
                    rel = raw
                if not rel:
                    continue
                child = rel.split("/")[0]
                if child in seen:
                    continue
                seen.add(child)
                parts = rel.split("/")
                is_dir = len(parts) > 1 or member.isdir()
                vpath = self._archive / (f"{prefix}/{child}" if prefix else child)
                items.append(FileItem(
                    name=child, path=vpath, is_dir=is_dir,
                    size=0 if is_dir else member.size,
                    modified=float(member.mtime),
                ))
        return items

    def _stat_tar(self, internal: str) -> FileItem:
        with tarfile.open(self._archive) as tf:
            members = tf.getmembers()
            for m in members:
                if m.name.rstrip("/") == internal:
                    return FileItem(
                        name=Path(internal).name, path=self._archive / internal,
                        is_dir=m.isdir(), size=0 if m.isdir() else m.size,
                        modified=float(m.mtime),
                    )
            # Virtual dir
            prefix = internal + "/"
            if any(m.name.startswith(prefix) for m in members):
                return FileItem(
                    name=Path(internal).name, path=self._archive / internal,
                    is_dir=True, size=0, modified=0.0,
                )
        raise KeyError(internal)


def _is_tar(path: Path) -> bool:
    s = path.suffixes
    return s[-1:] == [".tar"] or s[-2:] == [".tar", ".gz"]
