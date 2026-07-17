"""Unit tests for WorkspaceStore."""
from __future__ import annotations

import json

import pytest

from biome_fm.models.workspace_store import WorkspaceStore


@pytest.fixture
def store(tmp_path):
    return WorkspaceStore(tmp_path / "workspaces.json")


def test_save_load_roundtrip(store):
    store.save("home", ["/a", "/b"], ["/c"])
    data = store.load("home")
    assert data == {"left": ["/a", "/b"], "right": ["/c"]}


def test_list_names_sorted(store):
    store.save("zebra", [], [])
    store.save("apple", [], [])
    store.save("mango", [], [])
    assert store.list_names() == ["apple", "mango", "zebra"]


def test_delete_removes(store):
    store.save("ws1", ["/x"], [])
    store.delete("ws1")
    assert store.load("ws1") is None
    assert "ws1" not in store.list_names()


def test_load_unknown_returns_none(store):
    assert store.load("nonexistent") is None


def test_missing_file_returns_empty(tmp_path):
    s = WorkspaceStore(tmp_path / "sub" / "workspaces.json")
    assert s.list_names() == []
    assert s.load("x") is None


def test_corrupt_file_returns_empty(tmp_path):
    p = tmp_path / "workspaces.json"
    p.write_text("not json")
    s = WorkspaceStore(p)
    assert s.list_names() == []


def test_overwrite_existing(store):
    store.save("ws", ["/old"], [])
    store.save("ws", ["/new"], ["/extra"])
    assert store.load("ws") == {"left": ["/new"], "right": ["/extra"]}
