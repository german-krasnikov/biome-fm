"""Sync presenter — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus

Direction = Literal["left_to_right", "right_to_left", "newer_wins"]

# Each tuple is (src_path, dest_dir); caller builds CopyCmd with VFS.
SyncPair = tuple[Path, Path]

_LEFT_TO_RIGHT = {CompareStatus.LEFT_ONLY, CompareStatus.NEWER_LEFT, CompareStatus.DIFF_SIZE}
_RIGHT_TO_LEFT = {CompareStatus.RIGHT_ONLY, CompareStatus.NEWER_RIGHT, CompareStatus.DIFF_SIZE}


def build_sync_commands(
    entries: list[CompareEntry],
    direction: Direction,
    left_root: Path,
    right_root: Path,
) -> list[SyncPair]:
    """Return (src, dest_dir) pairs needed to synchronise two directories."""
    pairs: list[SyncPair] = []
    for e in entries:
        if e.status == CompareStatus.EQUAL:
            continue
        if direction == "left_to_right":
            if e.status in _LEFT_TO_RIGHT and e.left:
                pairs.append((e.left.path, right_root))
        elif direction == "right_to_left":
            if e.status in _RIGHT_TO_LEFT and e.right:
                pairs.append((e.right.path, left_root))
        elif direction == "newer_wins":
            if e.status in (CompareStatus.LEFT_ONLY, CompareStatus.NEWER_LEFT) and e.left:
                pairs.append((e.left.path, right_root))
            elif e.status in (CompareStatus.RIGHT_ONLY, CompareStatus.NEWER_RIGHT) and e.right:
                pairs.append((e.right.path, left_root))
    return pairs
