"""Tests for large file finder scan logic (F331)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.views.large_file_dialog import scan_large_files


def _write(p: Path, size: int) -> Path:
    p.write_bytes(b"x" * size)
    return p


def test_scan_finds_largest_files(tmp_path):
    _write(tmp_path / "small.bin", 100)
    _write(tmp_path / "medium.bin", 1000)
    _write(tmp_path / "large.bin", 5000)

    results = scan_large_files(tmp_path, min_bytes=0, limit=10)

    assert len(results) == 3
    # sorted largest first
    assert results[0][1] == 5000
    assert results[1][1] == 1000
    assert results[2][1] == 100


def test_min_size_filter(tmp_path):
    _write(tmp_path / "tiny.txt", 10)
    _write(tmp_path / "big.txt", 2_000_000)

    results = scan_large_files(tmp_path, min_bytes=1_000_000, limit=100)

    assert len(results) == 1
    assert results[0][1] == 2_000_000


def test_limit_respected(tmp_path):
    for i in range(10):
        _write(tmp_path / f"f{i}.bin", (i + 1) * 100)

    results = scan_large_files(tmp_path, min_bytes=0, limit=3)
    assert len(results) == 3
    # must be the 3 largest
    assert results[0][1] == 1000
    assert results[1][1] == 900
    assert results[2][1] == 800


def test_scan_empty_dir(tmp_path):
    assert scan_large_files(tmp_path) == []
