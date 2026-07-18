"""VFS Router — transparent dispatch by path type."""
from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from biome_fm.models.archive_vfs import ArchiveVFS
from biome_fm.models.file_item import FileItem
from biome_fm.models.remote_cache import RemoteListCache
from biome_fm.models.vfs import LocalVFS

if TYPE_CHECKING:
    from biome_fm.event_bus import EventBus
    from biome_fm.plugins.manager import PluginManager

_BUILTIN_EXTENSIONS: frozenset[str] = frozenset({"zip", "tar", "tar.gz", "tar.bz2", "tar.xz"})
# Detects URI-like strings. Path("sftp://host/p") → "sftp:/host/p" on POSIX, so
# we match single-slash form too (one-colon-slash is enough).
_URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*:/")


class VFSRouter:
    """Selects VFS by path. Drop-in replacement for LocalVFS."""

    def __init__(self, plugin_manager: PluginManager | None = None, bus: EventBus | None = None) -> None:
        self._local = LocalVFS()
        self._cache: dict[Path, ArchiveVFS] = {}
        self._pm = plugin_manager
        self._remote: dict[str, object] = {}  # key = "scheme://user@host:port"
        self._remote_lock = threading.Lock()
        self._rcache = RemoteListCache()
        self._bus = bus

    def _archive_extensions(self) -> frozenset[str]:
        exts = set(_BUILTIN_EXTENSIONS)
        if self._pm is not None:
            for lst in self._pm.hook.extra_archive_extensions():
                exts.update(lst)
        return frozenset(exts)

    def _resolve(self, path: Path):
        if self._pm is not None:
            plugin_vfs = self._pm.hook.provide_vfs(path=str(path))
            if plugin_vfs:
                return plugin_vfs, path
        raw = str(path)
        if _URI_RE.match(raw):
            return self._get_remote_vfs(raw)
        root = _find_archive_root(path, self._archive_extensions())
        if root is None:
            return self._local, path
        if root not in self._cache:
            self._cache[root] = ArchiveVFS(root)
        return self._cache[root], path

    def _get_remote_vfs(self, raw_path: str) -> tuple[object, Path]:
        from biome_fm.presenters.uri_parser import detect_scheme, parse_uri

        # Path("sftp://host/p") → "sftp:/host/p" on POSIX — restore double slash
        if "://" not in raw_path:
            raw_path = raw_path.replace(":/", "://", 1)

        scheme = detect_scheme(raw_path)
        if scheme is None:
            raise ValueError(f"Unknown scheme in: {raw_path}")

        parsed = parse_uri(raw_path)
        key = f"{scheme}://{parsed.username or ''}@{parsed.host}:{parsed.port or ''}"

        with self._remote_lock:
            if key not in self._remote:
                self._remote[key] = self._create_vfs(scheme, raw_path, parsed)
                if self._bus is not None:
                    from biome_fm.event_bus import RemoteConnected
                    self._bus.publish(RemoteConnected(scheme=scheme, host=parsed.host))
            vfs = self._remote[key]

        return vfs, self._remote_path(scheme, raw_path, parsed)

    def _create_vfs(self, scheme: str, raw_path: str, parsed) -> object:
        if scheme == "rclone":
            from biome_fm.models.rclone_vfs import RcloneVFS
            after = raw_path[len("rclone://"):]
            remote = after[: after.index(":") + 1]  # e.g. "gdrive:"
            return RcloneVFS(remote)  # type: ignore[return-value]
        elif scheme in ("sftp", "ssh"):
            from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs
            vfs = SFTPVfs(SFTPSession(
                host=parsed.host,
                port=parsed.port or 22,
                user=parsed.username or "",
            ))
            vfs.connect()
            return vfs
        else:
            from biome_fm.models.credential_store import get_credential
            from biome_fm.models.fsspec_vfs import FsspecVFS
            cred = get_credential(f"biome-fm/{scheme}", parsed.host)
            opts: dict = {"token": cred} if cred else {}
            return FsspecVFS(f"{scheme}://{parsed.host}", **opts)  # type: ignore[return-value]

    @staticmethod
    def _remote_path(scheme: str, raw_path: str, parsed) -> Path:
        if scheme == "rclone":
            after = raw_path[len("rclone://"):]
            path_str = after[after.index(":") + 1:] or "/"
            return Path(path_str)
        return Path(parsed.path)

    def disconnect(self, key: str) -> None:
        """Remove connection from cache and close it."""
        with self._remote_lock:
            vfs = self._remote.pop(key, None)
        if vfs is not None and hasattr(vfs, "disconnect"):
            vfs.disconnect()
        if vfs is not None and self._bus is not None:
            from biome_fm.event_bus import RemoteDisconnected
            # key format: "scheme://user@host:port"
            scheme, rest = key.split("://", 1)
            host = rest.split("@")[-1].split(":")[0]
            self._bus.publish(RemoteDisconnected(scheme=scheme, host=host))

    def listdir(self, path: Path) -> list[FileItem]:
        vfs, p = self._resolve(path)
        if vfs is self._local or isinstance(vfs, ArchiveVFS):
            return vfs.listdir(p)
        # Remote path — use TTL cache
        cached = self._rcache.get(path)
        if cached is not None:
            return cached
        items = vfs.listdir(p)
        self._rcache.set(path, items)
        return items

    def stat(self, path: Path) -> FileItem:
        vfs, p = self._resolve(path)
        return vfs.stat(p)

    def read_bytes(self, path: Path) -> bytes:
        vfs, p = self._resolve(path)
        return vfs.read_bytes(p)

    def exists(self, path: Path) -> bool:
        vfs, p = self._resolve(path)
        return vfs.exists(p)

    def open_file(self, path: Path):
        vfs, p = self._resolve(path)
        return vfs.open_file(p)

    def copy(self, src: Path, dst: Path) -> None:
        vfs, _ = self._resolve(src)
        if isinstance(vfs, ArchiveVFS):
            self._extract(vfs, src, dst)
        else:
            vfs.copy(src, dst)

    def _extract(self, vfs: ArchiveVFS, src: Path, dst: Path) -> None:
        try:
            info = vfs.stat(src)
            is_dir = info.is_dir
        except (KeyError, OSError):
            is_dir = False
        if is_dir:
            dst.mkdir(parents=True, exist_ok=True)
            for item in vfs.listdir(src):
                self._extract(vfs, item.path, dst / item.name)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with vfs.open_file(src) as f:
                dst.write_bytes(f.read())

    def move(self, src: Path, dst: Path) -> None:
        vfs, _ = self._resolve(src)
        vfs.move(src, dst)
        if _URI_RE.match(str(src)):
            self._rcache.invalidate(src.parent)
        if _URI_RE.match(str(dst)):
            self._rcache.invalidate(dst.parent)

    def delete(self, path: Path) -> None:
        vfs, p = self._resolve(path)
        vfs.delete(p)
        if _URI_RE.match(str(path)):
            self._rcache.invalidate(path.parent)

    def mkdir(self, path: Path) -> None:
        vfs, p = self._resolve(path)
        vfs.mkdir(p)
        if _URI_RE.match(str(path)):
            self._rcache.invalidate(path.parent)


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
