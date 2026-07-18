from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlparse


@dataclass
class BookmarkNode:
    kind: Literal["dir", "submenu", "separator", "search"]
    path: Path | None = None
    name: str = ""
    children: list[BookmarkNode] = field(default_factory=list)


def display_label(node: BookmarkNode) -> str:
    if node.kind == "dir":
        if node.name:
            return node.name
        if node.path is not None:
            return node.path.name or str(node.path)
        return ""
    if node.kind == "submenu":
        return node.name
    if node.kind == "search":
        return node.name or "Search"
    return "──────────"


def parse_search_uri(uri: str) -> dict[str, str]:
    """Parse search URI → params dict.

    Handles both `search://name=*.py&content=TODO` and the Path-normalized
    form `search:/name=*.py&content=TODO` (Path() collapses double slashes).
    """
    parsed = urlparse(uri)
    # query > netloc > path (Path() normalizes // → /, params end up in path)
    raw = parsed.query or parsed.netloc or parsed.path.lstrip("/")
    return {k: v[0] for k, v in parse_qs(raw).items()}
