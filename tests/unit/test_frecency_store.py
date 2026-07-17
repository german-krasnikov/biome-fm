"""Unit tests for FrecencyStore — no Qt."""
from __future__ import annotations

import time
from pathlib import Path

from biome_fm.models.frecency_store import FrecencyEntry, FrecencyStore


def test_record_increments_visits(tmp_path):
    store = FrecencyStore(tmp_path / "frecency.json")
    p = Path("/home/user/docs")
    store.record(p)
    store.record(p)
    entries = store.top(10)
    assert entries[0].path == p
    assert entries[0].visits == 2


def test_score_recent_beats_old(tmp_path):
    store = FrecencyStore(tmp_path / "frecency.json")
    old = Path("/old/path")
    recent = Path("/recent/path")
    # Both 1 visit; old visited a day ago, recent just now
    store._data[str(old)] = {"visits": 1, "last_visit": time.time() - 86400}
    store.record(recent)
    entries = store.top(10)
    assert entries[0].path == recent


def test_top_n_sorted_by_score(tmp_path):
    store = FrecencyStore(tmp_path / "frecency.json")
    for i in range(5):
        for _ in range(i + 1):
            store.record(Path(f"/dir/{i}"))
    results = store.top(5)
    scores = [store.score(e) for e in results]
    assert scores == sorted(scores, reverse=True)


def test_max_200_entries_evicted(tmp_path):
    store = FrecencyStore(tmp_path / "frecency.json")
    for i in range(200):
        store._data[f"/dir/{i}"] = {"visits": 1, "last_visit": time.time() - i}
    # Adding one more should evict the worst entry
    store.record(Path("/dir/new"))
    assert len(store._data) <= 200
