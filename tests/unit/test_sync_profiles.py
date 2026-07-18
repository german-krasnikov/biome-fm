"""Unit tests for SyncProfileStore — pure TOML persistence, no Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.sync_profiles import SyncProfile, SyncProfileStore


@pytest.fixture
def store(tmp_path: Path) -> SyncProfileStore:
    return SyncProfileStore(tmp_path / "sync_profiles.toml")


def test_save_load_sync_preset(store: SyncProfileStore) -> None:
    p = SyncProfile(name="work", src="/src", dst="/dst", exclude=["*.pyc"], mirror=True)
    store.add(p)
    store.save()

    s2 = SyncProfileStore(store._path)
    s2.load()
    loaded = s2.get("work")
    assert loaded.src == "/src"
    assert loaded.dst == "/dst"
    assert loaded.exclude == ["*.pyc"]
    assert loaded.mirror is True


def test_profile_round_trip(store: SyncProfileStore) -> None:
    store.add(SyncProfile(name="a", src="/a", dst="/b", exclude=["*.log", "tmp/"], mirror=False))
    store.save()

    s2 = SyncProfileStore(store._path)
    s2.load()
    p = s2.get("a")
    assert p.name == "a"
    assert p.exclude == ["*.log", "tmp/"]
    assert p.mirror is False


def test_list_presets(store: SyncProfileStore) -> None:
    for n in ("x", "y", "z"):
        store.add(SyncProfile(name=n, src=f"/{n}", dst="/out"))
    assert len(store.list_all()) == 3


def test_delete_preset(store: SyncProfileStore) -> None:
    store.add(SyncProfile(name="tmp", src="/x", dst="/y"))
    store.delete("tmp")
    assert store.list_all() == []


def test_unknown_preset_raises(store: SyncProfileStore) -> None:
    with pytest.raises(KeyError):
        store.get("nope")


def test_windows_paths_round_trip(store: SyncProfileStore) -> None:
    """Backslashes in Windows paths must survive TOML serialization."""
    store.add(SyncProfile(name="win", src=r"C:\Users\foo", dst=r"D:\Backup"))
    store.save()
    s2 = SyncProfileStore(store._path)
    s2.load()
    p = s2.get("win")
    assert p.src == r"C:\Users\foo"
    assert p.dst == r"D:\Backup"
