"""SFTP VFS stub. Requires paramiko. VFSRouter wiring deferred."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import paramiko as _paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _paramiko = None
    _HAS_PARAMIKO = False

_URI_RE = re.compile(r"sftp://(?:([^@]+)@)?([^/:]+)(?::(\d+))?(/.*)$")


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
    """SFTP VFS. Stub — listdir/stat raise NotImplementedError when paramiko absent."""

    def __init__(self, session: SFTPSession) -> None:
        self._session = session
        self._client = None
        self._sftp = None

    @staticmethod
    def available() -> bool:
        return _HAS_PARAMIKO

    def connect(self) -> None:
        if not _HAS_PARAMIKO:
            raise RuntimeError("paramiko not installed")
        client = _paramiko.SSHClient()
        client.set_missing_host_key_policy(_paramiko.AutoAddPolicy())
        client.connect(
            self._session.host,
            port=self._session.port,
            username=self._session.user or None,
        )
        self._client = client
        self._sftp = client.open_sftp()

    def listdir(self, path: Path) -> list:
        # ponytail: stub, returns [] — wire paramiko SFTPClient.listdir_attr when needed
        if not _HAS_PARAMIKO:
            raise RuntimeError("paramiko not installed")
        return []

    def disconnect(self) -> None:
        if self._sftp:
            self._sftp.close()
        if self._client:
            self._client.close()
        self._sftp = None
        self._client = None
