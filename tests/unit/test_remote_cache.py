"""F234 — RemoteListCache TTL tests."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str) -> FileItem:
    return FileItem(name=name, path=Path(f"/remote/{name}"), is_dir=False, size=0, modified=0.0)


class TestRemoteListCache:
    def setup_method(self):
        from biome_fm.models.remote_cache import RemoteListCache
        self.Cache = RemoteListCache

    def test_cache_hit_returns_same_items(self):
        cache = self.Cache(ttl=60.0)
        items = [_item("a"), _item("b")]
        cache.set(Path("/remote/path"), items)
        result = cache.get(Path("/remote/path"))
        assert result == items

    def test_cache_hit_returns_copy(self):
        """Returned list must be a copy so callers can't mutate the cache."""
        cache = self.Cache(ttl=60.0)
        items = [_item("a")]
        cache.set(Path("/p"), items)
        result = cache.get(Path("/p"))
        assert result is not items

    def test_cache_miss_returns_none(self):
        cache = self.Cache(ttl=60.0)
        assert cache.get(Path("/missing")) is None

    def test_cache_miss_after_ttl(self):
        cache = self.Cache(ttl=0.01)
        cache.set(Path("/p"), [_item("a")])
        time.sleep(0.02)
        assert cache.get(Path("/p")) is None

    def test_invalidate_clears_single_entry(self):
        cache = self.Cache(ttl=60.0)
        cache.set(Path("/a"), [_item("x")])
        cache.set(Path("/b"), [_item("y")])
        cache.invalidate(Path("/a"))
        assert cache.get(Path("/a")) is None
        assert cache.get(Path("/b")) is not None

    def test_invalidate_all(self):
        cache = self.Cache(ttl=60.0)
        cache.set(Path("/a"), [_item("x")])
        cache.set(Path("/b"), [_item("y")])
        cache.invalidate()
        assert cache.get(Path("/a")) is None
        assert cache.get(Path("/b")) is None

    def test_thread_safety(self):
        cache = self.Cache(ttl=60.0)
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for i in range(100):
                    p = Path(f"/path/{i % 5}")
                    cache.set(p, [_item(f"item{i}")])
                    cache.get(p)
                    if i % 10 == 0:
                        cache.invalidate(p)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
