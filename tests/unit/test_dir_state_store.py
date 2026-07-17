"""Unit tests for DirStateStore — no Qt."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.models.dir_state_store import DirStateStore
from biome_fm.models.view_state import ViewState


def test_save_and_load_round_trip(tmp_path):
    store = DirStateStore(tmp_path / "dir_state.json")
    p = Path("/home/user/docs")
    state = ViewState(sort_col=2, sort_asc=False, filter="*.py")
    store.save(p, state)
    loaded = store.load(p)
    assert loaded == state


def test_missing_path_returns_none(tmp_path):
    store = DirStateStore(tmp_path / "dir_state.json")
    assert store.load(Path("/nonexistent/path")) is None


def test_lru_eviction_at_500(tmp_path):
    store = DirStateStore(tmp_path / "dir_state.json")
    first = Path("/dir/0")
    store.save(first, ViewState())
    for i in range(1, 500):
        store.save(Path(f"/dir/{i}"), ViewState(sort_col=i % 4))
    # After 500 saves (0..499), adding one more should evict the oldest (first)
    store.save(Path("/dir/500"), ViewState())
    assert store.load(first) is None


def test_atomic_write(tmp_path):
    path = tmp_path / "dir_state.json"
    store = DirStateStore(path)
    store.save(Path("/foo"), ViewState(sort_col=1))
    store._flush()
    # File must exist and be valid JSON
    assert path.exists()
    data = json.loads(path.read_text())
    assert "/foo" in data
