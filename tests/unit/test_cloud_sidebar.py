"""F303 — CloudConnectionStore tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.cloud_connection_store import CloudConnectionStore


def test_cloud_connection_store_save_load(tmp_path: Path) -> None:
    store = CloudConnectionStore(tmp_path / "connections.json")
    store.add("s3://my-bucket/data")
    store.save()

    store2 = CloudConnectionStore(tmp_path / "connections.json")
    store2.load()
    assert "s3://my-bucket/data" in store2.list()


def test_cloud_connection_store_list(tmp_path: Path) -> None:
    store = CloudConnectionStore(tmp_path / "connections.json")
    store.add("s3://bucket-a")
    store.add("ftp://server/path")
    assert store.list() == ["s3://bucket-a", "ftp://server/path"]
