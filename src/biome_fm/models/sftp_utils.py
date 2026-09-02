"""SFTP helpers shared between sftp_vfs and other modules."""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass

_URI_RE = re.compile(r"sftp://(?:([^@]+)@)?([^/:]+)(?::(\d+))?(/.*)$")


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
    # ponytail: POSIX quoting only; add Windows-aware quoting if Windows SSH jump hosts required
    user_prefix = f"{shlex.quote(jump_user)}@" if jump_user else ""
    return (
        f"ssh -W {shlex.quote(target_host)}:{int(target_port)}"
        f" -p {int(jump_port)} {user_prefix}{shlex.quote(jump_host)}"
    )


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
