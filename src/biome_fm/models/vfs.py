"""VFS protocol and local filesystem implementation."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol

from biome_fm.models.file_item import FileItem


class VFSProtocol(Protocol):
    def listdir(self, path: Path) -> list[FileItem]: ...
    def stat(self, path: Path) -> FileItem: ...
    def read_bytes(self, path: Path) -> bytes: ...
    def copy(self, src: Path, dst: Path) -> None: ...
    def move(self, src: Path, dst: Path) -> None: ...
    def delete(self, path: Path) -> None: ...
    def mkdir(self, path: Path) -> None: ...
    def exists(self, path: Path) -> bool: ...


class LocalVFS:
    def listdir(self, path: Path) -> list[FileItem]:
        items = []
        for entry in os.scandir(path):
            try:
                st = entry.stat()
                items.append(FileItem(
                    name=entry.name,
                    path=Path(entry.path),
                    is_dir=entry.is_dir(),
                    size=st.st_size if not entry.is_dir() else 0,
                    modified=st.st_mtime,
                    is_symlink=entry.is_symlink(),
                ))
            except OSError:
                continue
        return items

    def stat(self, path: Path) -> FileItem:
        st = path.stat()
        return FileItem(
            name=path.name, path=path, is_dir=path.is_dir(),
            size=st.st_size, modified=st.st_mtime,
        )

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def copy(self, src: Path, dst: Path) -> None:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            try:
                with open(src, "rb") as fin, open(dst, "wb") as fout:
                    os.sendfile(fout.fileno(), fin.fileno(), 0, src.stat().st_size)
                shutil.copystat(src, dst)
            except (AttributeError, OSError):
                shutil.copy2(src, dst)

    def move(self, src: Path, dst: Path) -> None:
        shutil.move(str(src), str(dst))

    def delete(self, path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def mkdir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def exists(self, path: Path) -> bool:
        return path.exists()
