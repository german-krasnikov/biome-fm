from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class BookmarkNode:
    kind: Literal["dir", "submenu", "separator"]
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
    return "──────────"
