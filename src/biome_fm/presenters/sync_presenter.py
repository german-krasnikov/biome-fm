"""Sync presenter — pure Python, no Qt."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus

Direction = Literal["left_to_right", "right_to_left", "newer_wins"]

# Each tuple is (src_path, dest_dir); caller builds CopyCmd with VFS.
SyncPair = tuple[Path, Path]

_LEFT_TO_RIGHT = {CompareStatus.LEFT_ONLY, CompareStatus.NEWER_LEFT, CompareStatus.DIFF_SIZE}
_RIGHT_TO_LEFT = {CompareStatus.RIGHT_ONLY, CompareStatus.NEWER_RIGHT, CompareStatus.DIFF_SIZE}


@dataclass
class SyncOp:
    action: str  # "copy_left_to_right" | "copy_right_to_left" | "delete_orphan"
    src: Path
    dst: Path
    size: int = field(default=0)


def _excluded(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def preview_sync(
    entries: list[CompareEntry],
    direction: Direction,
    left_root: Path,
    right_root: Path,
    exclude: list[str] | None = None,
    mirror: bool = False,
) -> list[SyncOp]:
    """Return planned SyncOp list without touching the filesystem."""
    excl = exclude or []
    ops: list[SyncOp] = []
    for e in entries:
        if excl and _excluded(e.name, excl):
            continue
        if e.status == CompareStatus.EQUAL:
            continue
        if direction == "left_to_right":
            if e.status in _LEFT_TO_RIGHT and e.left:
                ops.append(SyncOp("copy_left_to_right", e.left.path, right_root, e.left.size))
            elif mirror and e.status == CompareStatus.RIGHT_ONLY and e.right:
                ops.append(SyncOp("delete_orphan", e.right.path, right_root))
        elif direction == "right_to_left":
            if e.status in _RIGHT_TO_LEFT and e.right:
                ops.append(SyncOp("copy_right_to_left", e.right.path, left_root, e.right.size))
            elif mirror and e.status == CompareStatus.LEFT_ONLY and e.left:
                ops.append(SyncOp("delete_orphan", e.left.path, left_root))
        elif direction == "newer_wins":
            if e.status in (CompareStatus.LEFT_ONLY, CompareStatus.NEWER_LEFT) and e.left:
                ops.append(SyncOp("copy_left_to_right", e.left.path, right_root, e.left.size))
            elif e.status in (CompareStatus.RIGHT_ONLY, CompareStatus.NEWER_RIGHT) and e.right:
                ops.append(SyncOp("copy_right_to_left", e.right.path, left_root, e.right.size))
            elif e.status == CompareStatus.DIFF_SIZE and e.left and e.right:
                if e.left.modified >= e.right.modified:
                    ops.append(SyncOp("copy_left_to_right", e.left.path, right_root, e.left.size))
                else:
                    ops.append(SyncOp("copy_right_to_left", e.right.path, left_root, e.right.size))
    return ops


def build_sync_commands(
    entries: list[CompareEntry],
    direction: Direction,
    left_root: Path,
    right_root: Path,
    exclude: list[str] | None = None,
    mirror: bool = False,
) -> list[SyncPair]:
    """Return (src, dest_dir) pairs for copy ops only (delete_orphan excluded)."""
    return [
        (op.src, op.dst)
        for op in preview_sync(entries, direction, left_root, right_root, exclude=exclude, mirror=mirror)
        if op.action != "delete_orphan"
    ]
