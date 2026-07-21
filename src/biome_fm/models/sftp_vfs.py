"""SFTP VFS. Requires paramiko (optional dep)."""
from __future__ import annotations

import logging
import re
import stat
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

try:
    import paramiko as _paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _paramiko = None  # type: ignore[assignment]
    _HAS_PARAMIKO = False

_URI_RE = re.compile(r"sftp://(?:([^@]+)@)?([^/:]+)(?::(\d+))?(/.*)$")
_SSH_ERRORS: tuple[type[Exception], ...] = (ConnectionError, EOFError)
_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SFTPSession:
    host: str
    port: int = 22
    user: str = ""
    remote_path: str = "/"
    auto_add_host_key: bool = False
    proxy_command: str = ""


def make_jump_proxy_command(
    jump_host: str, jump_port: int, jump_user: str, target_host: str, target_port: int
) -> str:
    user_prefix = f"{jump_user}@" if jump_user else ""
    return f"ssh -W {target_host}:{target_port} -p {jump_port} {user_prefix}{jump_host}"


def parse_sftp_uri(uri: str) -> SFTPSession | None:
    m = _URI_RE.match(uri)
    if not m:
        return None
    user, host, port, path = m.groups()
    return SFTPSession(
        host=host,
        port=int(port or 22),
        user=user or "",
        remote_path=path or "/",
    )


class SFTPVfs:
    """SFTP VFS backed by paramiko. Raises RuntimeError when paramiko absent."""

    def __init__(self, session: SFTPSession, max_channels: int = 4) -> None:
        self._session = session
        self._client = None
        self._max_channels = max_channels
        self._channels: list = []                             # pool of idle SFTPClient channels
        self._semaphore = threading.Semaphore(max_channels)   # limits concurrent channel count
        self._lock = threading.Lock()

    def _get_channel(self):
        """Acquire a fresh or pooled channel (blocks at max_channels)."""
        if not _HAS_PARAMIKO:
            raise RuntimeError("Install paramiko for SFTP support: pip install paramiko")
        if self._client is None:
            raise RuntimeError("Not connected — call connect() first")
        self._semaphore.acquire()
        with self._lock:
            if self._channels:
                return self._channels.pop()
        return self._client.open_sftp()  # type: ignore[union-attr]

    def _return_channel(self, channel) -> None:
        """Return a channel to the pool and release the semaphore slot."""
        with self._lock:
            self._channels.append(channel)
        self._semaphore.release()

    @staticmethod
    def available() -> bool:
        return _HAS_PARAMIKO

    def connect(self) -> None:
        if not _HAS_PARAMIKO:
            raise RuntimeError("Install paramiko for SFTP support: pip install paramiko")
        client = _paramiko.SSHClient()
        if self._session.auto_add_host_key:
            _log.warning(
                "SFTP: auto-accepting host keys for %s — MITM risk", self._session.host
            )
            client.set_missing_host_key_policy(_paramiko.AutoAddPolicy())
        else:
            client.set_missing_host_key_policy(_paramiko.RejectPolicy())
        sock = (
            _paramiko.ProxyCommand(self._session.proxy_command)
            if self._session.proxy_command
            else None
        )
        client.connect(
            self._session.host,
            port=self._session.port,
            username=self._session.user or None,
            sock=sock,
        )
        self._client = client
        transport = client.get_transport()
        if transport is not None:
            transport.set_keepalive(30)
        # Seed pool with one channel
        with self._lock:
            self._channels = [client.open_sftp()]

    def _reconnect(self) -> None:
        with self._lock:
            for ch in self._channels:
                try:
                    ch.close()
                except Exception:
                    pass
            self._channels.clear()
        if self._client:
            self._client.close()
        self._client = None
        self.connect()

    def _with_reconnect(self, fn, *args):
        """Acquire channel, call fn(sftp, *args), retry up to 3x on SSH errors."""
        last_exc: Exception | None = None
        for attempt in range(4):
            # client may be None if a previous reconnect attempt failed
            if self._client is None:
                if attempt == 0:
                    if not _HAS_PARAMIKO:
                        raise RuntimeError(
                            "Install paramiko for SFTP support: pip install paramiko"
                        )
                    raise RuntimeError("Not connected — call connect() first")
                if attempt >= 3:
                    raise (last_exc or RuntimeError("Not connected"))
                time.sleep(2 ** attempt)
                try:
                    self._reconnect()
                except _SSH_ERRORS as exc:
                    last_exc = exc
                continue
            ch = self._get_channel()
            try:
                result = fn(ch, *args)
                self._return_channel(ch)
                return result
            except _SSH_ERRORS as exc:
                last_exc = exc
                try:
                    ch.close()
                except Exception:
                    pass
                self._semaphore.release()  # slot freed — channel discarded
                if attempt >= 3:
                    raise
                time.sleep(2 ** attempt)
                try:
                    self._reconnect()
                except _SSH_ERRORS:
                    pass  # reconnect failed; will retry on next loop

    def listdir(self, path: PurePosixPath) -> list:
        from biome_fm.models.file_item import FileItem

        def _do(sftp, p):
            attrs = sftp.listdir_attr(str(p))
            items = []
            for a in attrs:
                is_dir = bool(a.st_mode and stat.S_ISDIR(a.st_mode))
                mtime = datetime.fromtimestamp(a.st_mtime or 0) if a.st_mtime else None
                items.append(FileItem(
                    name=a.filename,
                    path=Path(str(p)) / a.filename,
                    is_dir=is_dir,
                    size=a.st_size or 0,
                    modified=mtime,
                ))
            return items

        return self._with_reconnect(_do, path)

    def stat(self, path: PurePosixPath) -> "FileItem":
        from biome_fm.models.file_item import FileItem

        def _do(sftp, p):
            a = sftp.stat(str(p))
            is_dir = bool(a.st_mode and stat.S_ISDIR(a.st_mode))
            return FileItem(
                name=PurePosixPath(p).name,
                path=Path(str(p)),
                is_dir=is_dir,
                size=a.st_size or 0,
                modified=float(a.st_mtime or 0.0),
            )

        return self._with_reconnect(_do, path)

    def read_bytes(self, path: PurePosixPath) -> bytes:
        def _do(sftp, p):
            with sftp.open(str(p), "rb") as f:
                return f.read()

        return self._with_reconnect(_do, path)

    def write_bytes(self, path: PurePosixPath, data: bytes) -> None:
        def _do(sftp, p, d):
            with sftp.open(str(p), "wb") as f:
                f.write(d)

        self._with_reconnect(_do, path, data)

    def mkdir(self, path: PurePosixPath) -> None:
        def _do(sftp, p):
            sftp.mkdir(str(p))

        self._with_reconnect(_do, path)

    def remove(self, path: PurePosixPath) -> None:
        def _do(sftp, p):
            try:
                sftp.remove(str(p))
            except OSError:
                sftp.rmdir(str(p))

        self._with_reconnect(_do, path)

    def chmod(self, path: PurePosixPath, mode: int) -> None:
        def _do(sftp, p, m):
            sftp.chmod(str(p), m)

        self._with_reconnect(_do, path, mode)

    def utime(self, path: PurePosixPath, mtime: float) -> None:
        def _do(sftp, p, t):
            sftp.utime(str(p), (t, t))

        self._with_reconnect(_do, path, mtime)

    def open_read(self, path: PurePosixPath, offset: int = 0):
        import contextlib

        @contextlib.contextmanager
        def _cm():
            def _do(sftp, p):
                return sftp.open(str(p), "rb")

            fh = self._with_reconnect(_do, path)
            try:
                if offset:
                    fh.seek(offset)
                yield fh
            finally:
                fh.close()

        return _cm()

    def exec_find(self, remote_dir: str, name_pattern: str, timeout: int = 30) -> list[str]:
        """Run `find` on server, return list of absolute remote paths."""
        import shlex
        if self._client is None:
            raise RuntimeError("Not connected — call connect() first")
        cmd = f"find {shlex.quote(remote_dir)} -name {shlex.quote(name_pattern)} -maxdepth 20 2>/dev/null"
        _, stdout, _ = self._client.exec_command(cmd, timeout=timeout)
        return [line.strip() for line in stdout if line.strip()]

    def disconnect(self) -> None:
        with self._lock:
            for ch in self._channels:
                try:
                    ch.close()
                except Exception:
                    pass
            self._channels.clear()
        if self._client:
            self._client.close()
        self._client = None
