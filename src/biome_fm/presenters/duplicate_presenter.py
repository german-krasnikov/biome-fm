"""Duplicate file finder — pure Python, no Qt."""
from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DupGroup:
    hash: str
    paths: list[Path]
    size: int


def find_duplicates(root: Path, cancel: list[bool]) -> list[DupGroup]:
    """Group files under *root* by content hash. Returns groups with 2+ files."""
    by_size: dict[int, list[Path]] = defaultdict(list)
    for dirpath, _, files in os.walk(root):
        if cancel[0]:
            return []
        for f in files:
            p = Path(dirpath) / f
            try:
                by_size[p.stat().st_size].append(p)
            except OSError:
                pass

    by_hash: dict[str, list[Path]] = defaultdict(list)
    sizes: dict[str, int] = {}
    for sz, paths in by_size.items():
        if len(paths) < 2:
            continue
        if cancel[0]:
            return []
        for p in paths:
            h = _file_hash(p)
            if h:
                by_hash[h].append(p)
                sizes[h] = sz

    return [DupGroup(hash=h, paths=ps, size=sizes[h])
            for h, ps in by_hash.items() if len(ps) >= 2]


def _file_hash(p: Path) -> str | None:
    h = hashlib.md5(usedforsecurity=False)
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None
