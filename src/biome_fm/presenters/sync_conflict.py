"""Two-way sync conflict detection (F009)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from biome_fm.presenters.compare_presenter import CompareEntry


@dataclass
class SyncConflict:
    path: str
    left_mtime: float
    right_mtime: float


class SyncSnapshot:
    """Per sync-pair snapshot of {filename: {left_mtime, right_mtime}}."""

    def __init__(self, pair_key: str = "") -> None:
        self._pair_key = pair_key
        self._data: dict[str, dict[str, float]] = {}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        all_data: dict = json.loads(path.read_text()) if path.exists() else {}
        all_data[self._pair_key] = self._data
        path.write_text(json.dumps(all_data))

    @classmethod
    def load(cls, path: Path, pair_key: str) -> SyncSnapshot:
        snap = cls(pair_key)
        if path.exists():
            snap._data = json.loads(path.read_text()).get(pair_key, {})
        return snap

    @staticmethod
    def key_for(left_root: Path, right_root: Path) -> str:
        return f"{left_root}|{right_root}"


def find_conflicts(entries: list[CompareEntry], snapshot: SyncSnapshot) -> list[SyncConflict]:
    """Return entries where both sides changed since the last snapshot."""
    conflicts: list[SyncConflict] = []
    for e in entries:
        if e.left is None or e.right is None:
            continue
        prev = snapshot._data.get(e.name)
        if prev is None:
            continue  # new file — no conflict
        if e.left.modified != prev["left_mtime"] and e.right.modified != prev["right_mtime"]:
            conflicts.append(SyncConflict(e.name, e.left.modified, e.right.modified))
    return conflicts


def update_snapshot(entries: list[CompareEntry], snapshot: SyncSnapshot) -> None:
    """Record current mtimes for all two-sided entries."""
    for e in entries:
        if e.left is not None and e.right is not None:
            snapshot._data[e.name] = {"left_mtime": e.left.modified, "right_mtime": e.right.modified}
