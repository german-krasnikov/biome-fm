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


def find_duplicates(root: Path | list[Path], cancel: list[bool]) -> list[DupGroup]:
    """Group files under *root* (or multiple roots) by content hash. Returns groups with 2+ files."""
    roots = [root] if isinstance(root, Path) else list(root)
    by_size: dict[int, list[Path]] = defaultdict(list)
    for r in roots:
        for dirpath, _, files in os.walk(r):
            if cancel[0]:
                return []
            for f in files:
                p = Path(dirpath) / f
                try:
                    by_size[p.stat().st_size].append(p)
                except OSError:
                    pass

    # Stage 2: partial hash (4 KB) — filters out ~90% of full reads
    by_partial: dict[tuple[int, str], list[Path]] = defaultdict(list)
    for sz, paths in by_size.items():
        if len(paths) < 2:
            continue
        if cancel[0]:
            return []
        for p in paths:
            h = _partial_hash(p)
            if h:
                by_partial[(sz, h)].append(p)

    # Stage 3: full hash only on partial-hash matches
    by_hash: dict[str, list[Path]] = defaultdict(list)
    sizes: dict[str, int] = {}
    for (sz, _), paths in by_partial.items():
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


def _partial_hash(p: Path, n: int = 4096) -> str | None:
    """Hash only the first *n* bytes of *p*."""
    try:
        with open(p, "rb") as f:
            return hashlib.md5(f.read(n), usedforsecurity=False).hexdigest()
    except OSError:
        return None
