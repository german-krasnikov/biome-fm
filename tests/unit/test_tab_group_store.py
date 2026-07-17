"""TDD: TabGroupStore — no Qt."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.tab_group_store import TabGroupStore


def test_save_and_load(tmp_path: Path) -> None:
    store = TabGroupStore(tmp_path / "groups.json")
    store.save_group("work", [Path("/a"), Path("/b")])
    assert store.load_group("work") == [Path("/a"), Path("/b")]


def test_unknown_group_returns_empty(tmp_path: Path) -> None:
    store = TabGroupStore(tmp_path / "groups.json")
    assert store.load_group("nope") == []


def test_overwrite_existing(tmp_path: Path) -> None:
    store = TabGroupStore(tmp_path / "groups.json")
    store.save_group("g", [Path("/a")])
    store.save_group("g", [Path("/b")])
    assert store.load_group("g") == [Path("/b")]


def test_list_groups(tmp_path: Path) -> None:
    store = TabGroupStore(tmp_path / "groups.json")
    store.save_group("a", [Path("/x")])
    store.save_group("b", [Path("/y")])
    assert set(store.list_groups()) == {"a", "b"}


def test_delete_group(tmp_path: Path) -> None:
    store = TabGroupStore(tmp_path / "groups.json")
    store.save_group("g", [Path("/x")])
    store.delete_group("g")
    assert store.load_group("g") == []
    assert "g" not in store.list_groups()


def test_persists_across_instances(tmp_path: Path) -> None:
    p = tmp_path / "groups.json"
    TabGroupStore(p).save_group("saved", [Path("/a")])
    assert TabGroupStore(p).load_group("saved") == [Path("/a")]
