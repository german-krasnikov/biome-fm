"""SFTP VFS. Requires paramiko (optional dep)."""
from __future__ import annotations

import re
import stat
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


@dataclass(frozen=True)
class SFTPSession:
    host: str
    port: int = 22
    user: str = ""
    remote_path: str = "/"


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

    def __init__(self, session: SFTPSession) -> None:
        self._session = session
        self._client = None
        self._sftp = None

    @staticmethod
    def available() -> bool:
        return _HAS_PARAMIKO

    def connect(self) -> None:
        if not _HAS_PARAMIKO:
            raise RuntimeError("Install paramiko for SFTP support: pip install paramiko")
        client = _paramiko.SSHClient()
        client.set_missing_host_key_policy(_paramiko.WarningPolicy())
        client.connect(
            self._session.host,
            port=self._session.port,
            username=self._session.user or None,
        )
        self._client = client
        self._sftp = client.open_sftp()
        transport = client.get_transport()
        if transport is not None:
            transport.set_keepalive(30)

    def _require_sftp(self):
        if not _HAS_PARAMIKO:
            raise RuntimeError("Install paramiko for SFTP support: pip install paramiko")
        if self._sftp is None:
            raise RuntimeError("Not connected — call connect() first")
        return self._sftp

    def _reconnect(self) -> None:
        self._sftp = None
        self._client = None
        self.connect()

    def _with_reconnect(self, fn, *args):
        """Call fn(*args), retrying up to 3 times on SSH errors with exponential backoff."""
        for attempt in range(4):
            try:
                return fn(*args)
            except _SSH_ERRORS as exc:
                if attempt >= 3:
                    raise
                time.sleep(2 ** attempt)
                try:
                    self._reconnect()
                except _SSH_ERRORS:
                    pass  # reconnect failed; will retry fn on next loop

    def listdir(self, path: PurePosixPath) -> list:
        from biome_fm.models.file_item import FileItem
        sftp = self._require_sftp()

        def _do(p):
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

    def read_bytes(self, path: PurePosixPath) -> bytes:
        sftp = self._require_sftp()

        def _do(p):
            with sftp.open(str(p), "rb") as f:
                return f.read()

        return self._with_reconnect(_do, path)

    def write_bytes(self, path: PurePosixPath, data: bytes) -> None:
        sftp = self._require_sftp()

        def _do(p):
            with sftp.open(str(p), "wb") as f:
                f.write(data)

        self._with_reconnect(_do, path)

    def mkdir(self, path: PurePosixPath) -> None:
        self._require_sftp().mkdir(str(path))

    def remove(self, path: PurePosixPath) -> None:
        sftp = self._require_sftp()
        try:
            sftp.remove(str(path))
        except OSError:
            sftp.rmdir(str(path))

    def disconnect(self) -> None:
        if self._sftp:
            self._sftp.close()
        if self._client:
            self._client.close()
        self._sftp = None
        self._client = None
