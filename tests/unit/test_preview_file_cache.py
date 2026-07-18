"""Tests for PreviewFileCache (F305)."""
from __future__ import annotations

from pathlib import Path


class TestPreviewFileCache:
    def test_put_and_get(self, tmp_path):
        from biome_fm.models.preview_file_cache import PreviewFileCache

        cache = PreviewFileCache(tmp_path)
        p = Path("/remote/file.txt")
        result = cache.put(p, 1000.0, b"content")
        assert result.exists()
        assert result.read_bytes() == b"content"
        hit = cache.get(p, 1000.0)
        assert hit is not None
        assert hit.read_bytes() == b"content"

    def test_get_miss_returns_none(self, tmp_path):
        from biome_fm.models.preview_file_cache import PreviewFileCache

        cache = PreviewFileCache(tmp_path)
        assert cache.get(Path("/remote/missing.txt"), 999.0) is None

    def test_get_miss_on_different_mtime(self, tmp_path):
        from biome_fm.models.preview_file_cache import PreviewFileCache

        cache = PreviewFileCache(tmp_path)
        p = Path("/remote/file.txt")
        cache.put(p, 1000.0, b"old")
        assert cache.get(p, 2000.0) is None  # different mtime

    def test_evict_lru_keeps_total_under_limit(self, tmp_path):
        from biome_fm.models.preview_file_cache import PreviewFileCache

        # 1 MB limit — put 2 files × 600KB each → eviction must happen
        cache = PreviewFileCache(tmp_path, max_mb=1)
        data = b"x" * (600 * 1024)  # 600 KB
        cache.put(Path("/remote/a.bin"), 1.0, data)
        cache.put(Path("/remote/b.bin"), 2.0, data)
        cache.evict_lru()
        # After evict, total size ≤ 1 MB — oldest file should be gone
        hit_a = cache.get(Path("/remote/a.bin"), 1.0)
        hit_b = cache.get(Path("/remote/b.bin"), 2.0)
        # b is newer, should survive; a might be evicted
        assert hit_b is not None
        # total cached bytes ≤ max_mb
        total = sum(f.stat().st_size for f in tmp_path.iterdir() if f.is_file())
        assert total <= 1 * 1024 * 1024
