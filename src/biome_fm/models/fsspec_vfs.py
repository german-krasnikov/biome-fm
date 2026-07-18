"""fsspec VFS adapter — S3, FTP, WebDAV, and any fsspec-compatible protocol."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.file_item import FileItem

try:
    import fsspec
except ImportError:
    fsspec = None  # type: ignore[assignment]


def _mtime(info: dict) -> float:
    if (m := info.get("mtime")) is not None:
        return float(m)
    if (m := info.get("LastModified")) is not None:
        return m.timestamp() if hasattr(m, "timestamp") else float(m)
    return 0.0


def _info_to_item(info: dict) -> FileItem:
    name = info["name"].rstrip("/").split("/")[-1] or info["name"].rstrip("/")
    return FileItem(
        name=name,
        path=Path(info["name"].rstrip("/")),
        is_dir=info.get("type") == "directory",
        size=info.get("size") or 0,
        modified=_mtime(info),
    )


class FsspecVFS:
    """VFS adapter for any fsspec-compatible protocol (S3, FTP, WebDAV, etc.)."""

    def __init__(self, url: str, **storage_options) -> None:
        if fsspec is None:
            raise ImportError("Install fsspec: pip install fsspec")
        protocol = url.split("://")[0] if "://" in url else url
        self._fs = fsspec.filesystem(protocol, **storage_options)

    def listdir(self, path: Path) -> list[FileItem]:
        return [_info_to_item(i) for i in self._fs.ls(str(path), detail=True)]

    def stat(self, path: Path) -> FileItem:
        return _info_to_item(self._fs.info(str(path)))

    def exists(self, path: Path) -> bool:
        return self._fs.exists(str(path))

    def read_bytes(self, path: Path) -> bytes:
        return self._fs.cat_file(str(path))

    def copy(self, src: Path, dst: Path) -> None:
        src_s, dst_s = str(src), str(dst)
        if src.is_absolute() and src.exists():  # local → remote
            self._fs.put(src_s, dst_s)
        else:  # remote → local
            self._fs.get(src_s, dst_s)

    def move(self, src: Path, dst: Path) -> None:
        self._fs.mv(str(src), str(dst))

    def delete(self, path: Path) -> None:
        self._fs.rm(str(path), recursive=True)

    def write_bytes(self, path: Path, data: bytes) -> None:
        with self._fs.open(str(path), "wb") as f:
            f.write(data)

    def mkdir(self, path: Path) -> None:
        self._fs.makedirs(str(path), exist_ok=True)
