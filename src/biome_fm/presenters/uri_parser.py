"""URI parsing for path-bar navigation — F040."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

_KNOWN = {"sftp", "ssh", "s3", "ftp", "ftps", "webdav"}


@dataclass
class ParsedURI:
    scheme: str
    host: str
    port: int | None
    path: str
    username: str | None = None


def detect_scheme(text: str) -> str | None:
    if "://" in text:
        scheme = text.split("://", 1)[0].lower()
        if scheme in _KNOWN:
            return scheme
    return None


def parse_uri(text: str) -> ParsedURI:
    p = urlparse(text)
    try:
        port = p.port
    except ValueError:
        port = None
    return ParsedURI(scheme=p.scheme, host=p.hostname or "", port=port,
                     path=p.path, username=p.username)
