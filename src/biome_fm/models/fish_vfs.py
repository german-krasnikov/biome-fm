"""FISH VFS — Files over Shell. SSH exec_command fallback when SFTP unavailable."""
from __future__ import annotations

import shlex
from pathlib import Path, PurePosixPath

try:
    import paramiko as _paramiko
    _HAS_PARAMIKO = True
except ImportError:
    _paramiko = None  # type: ignore[assignment]
    _HAS_PARAMIKO = False

from biome_fm.models.file_item import FileItem
from biome_fm.models.ls_parser import parse_ls_line


class FISHVfs:
    """SSH exec_command VFS for devices without SFTP subsystem."""

    def __init__(self, host: str, port: int = 22, user: str = "",
                 key_path: str = "", proxy_command: str = "") -> None:
        if not _HAS_PARAMIKO:
            raise RuntimeError("Install paramiko: pip install paramiko")
        self._host = host
        self._port = port
        self._user = user
        self._key_path = key_path
        self._proxy_command = proxy_command
        self._client = None

    def connect(self) -> None:
        client = _paramiko.SSHClient()
        client.set_missing_host_key_policy(_paramiko.AutoAddPolicy())
        sock = _paramiko.ProxyCommand(self._proxy_command) if self._proxy_command else None
        kw: dict = dict(hostname=self._host, port=self._port, username=self._user or None, sock=sock)
        if self._key_path:
            kw["key_filename"] = self._key_path
        client.connect(**kw)
        self._client = client

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def _exec(self, cmd: str, timeout: int = 10) -> str:
        if self._client is None:
            raise RuntimeError("Not connected")
        _, stdout, _ = self._client.exec_command(cmd, timeout=timeout)
        return stdout.read().decode("utf-8", errors="replace")

    def listdir(self, path: PurePosixPath) -> list[FileItem]:
        out = self._exec(f"ls -la --time-style=long-iso {shlex.quote(str(path))} 2>/dev/null")
        items = []
        for line in out.splitlines():
            info = parse_ls_line(line)
            if info is None or info["name"] in (".", ".."):
                continue
            items.append(FileItem(
                name=info["name"],
                path=Path(str(path)) / info["name"],
                is_dir=info["is_dir"],
                size=info["size"],
                modified=info["mtime"],
            ))
        return items

    def read_bytes(self, path: PurePosixPath) -> bytes:
        if self._client is None:
            raise RuntimeError("Not connected")
        _, stdout, _ = self._client.exec_command(
            f"cat {shlex.quote(str(path))}", timeout=60
        )
        return stdout.read()
