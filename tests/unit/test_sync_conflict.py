"""Unit tests for two-way sync conflict detection (F009)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import CompareEntry, CompareStatus
from biome_fm.presenters.sync_conflict import (
    SyncConflict,
    SyncSnapshot,
    find_conflicts,
    update_snapshot,
)


def _fi(name: str, mtime: float) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=100, modified=mtime)


def _entry(name: str, left_mtime: float, right_mtime: float) -> CompareEntry:
    return CompareEntry(
        name=name,
        status=CompareStatus.DIFF_SIZE,
        left=_fi(name, left_mtime),
        right=_fi(name, right_mtime),
    )


# --- find_conflicts ---

def test_conflict_detected_both_modified():
    snap = SyncSnapshot()
    snap._data["file.txt"] = {"left_mtime": 1000.0, "right_mtime": 2000.0}
    entries = [_entry("file.txt", 1100.0, 2100.0)]  # both changed
    conflicts = find_conflicts(entries, snap)
    assert len(conflicts) == 1
    assert conflicts[0] == SyncConflict("file.txt", 1100.0, 2100.0)


def test_no_conflict_one_side_only():
    snap = SyncSnapshot()
    snap._data["file.txt"] = {"left_mtime": 1000.0, "right_mtime": 2000.0}
    entries = [_entry("file.txt", 1100.0, 2000.0)]  # only left changed
    assert find_conflicts(entries, snap) == []


def test_first_sync_no_conflicts():
    snap = SyncSnapshot()  # empty — no prior sync
    entries = [_entry("file.txt", 1000.0, 2000.0)]
    assert find_conflicts(entries, snap) == []


def test_left_only_entry_skipped():
    snap = SyncSnapshot()
    snap._data["file.txt"] = {"left_mtime": 1000.0, "right_mtime": 2000.0}
    entry = CompareEntry(
        name="file.txt",
        status=CompareStatus.LEFT_ONLY,
        left=_fi("file.txt", 1100.0),
        right=None,
    )
    assert find_conflicts([entry], snap) == []


# --- update_snapshot ---

def test_snapshot_persisted_after_sync():
    snap = SyncSnapshot()
    entries = [_entry("a.txt", 1000.0, 2000.0), _entry("b.txt", 3000.0, 4000.0)]
    update_snapshot(entries, snap)
    assert snap._data["a.txt"] == {"left_mtime": 1000.0, "right_mtime": 2000.0}
    assert snap._data["b.txt"] == {"left_mtime": 3000.0, "right_mtime": 4000.0}


def test_update_snapshot_skips_one_sided():
    snap = SyncSnapshot()
    entry = CompareEntry(
        name="orphan.txt",
        status=CompareStatus.LEFT_ONLY,
        left=_fi("orphan.txt", 999.0),
        right=None,
    )
    update_snapshot([entry], snap)
    assert "orphan.txt" not in snap._data


# --- save / load (round-trip) ---

def test_snapshot_round_trip(tmp_path: Path):
    snap_file = tmp_path / "snapshots.json"
    pair_key = "/left|/right"

    snap = SyncSnapshot(pair_key)
    snap._data["x.txt"] = {"left_mtime": 1.0, "right_mtime": 2.0}
    snap.save(snap_file)

    loaded = SyncSnapshot.load(snap_file, pair_key)
    assert loaded._data == {"x.txt": {"left_mtime": 1.0, "right_mtime": 2.0}}


def test_save_preserves_other_pairs(tmp_path: Path):
    snap_file = tmp_path / "snapshots.json"
    snap_file.write_text(json.dumps({"/other|/pair": {"z.txt": {"left_mtime": 9.0, "right_mtime": 8.0}}}))

    snap = SyncSnapshot("/left|/right")
    snap._data["a.txt"] = {"left_mtime": 1.0, "right_mtime": 2.0}
    snap.save(snap_file)

    raw = json.loads(snap_file.read_text())
    assert "/other|/pair" in raw  # not clobbered
    assert "/left|/right" in raw


def test_load_missing_file_returns_empty(tmp_path: Path):
    snap = SyncSnapshot.load(tmp_path / "nonexistent.json", "/a|/b")
    assert snap._data == {}
