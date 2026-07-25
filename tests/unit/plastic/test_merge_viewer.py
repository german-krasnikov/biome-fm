"""Unit tests for get_merge_sides in _diff.py — sidecar file approach."""
from __future__ import annotations

from pathlib import Path


def test_get_merge_sides_reads_sidecar_files(tmp_path):
    from biome_fm.plastic._diff import get_merge_sides
    f = tmp_path / "test.txt"
    f.write_text("local content")
    (tmp_path / "test.BASE.1.txt").write_text("base text")
    (tmp_path / "test.SOURCE.1.txt").write_text("source text")
    base, source, dest = get_merge_sides(f, tmp_path)
    assert base == "base text"
    assert source == "source text"
    assert dest == "local content"


def test_get_merge_sides_missing_sidecars_returns_empty(tmp_path):
    from biome_fm.plastic._diff import get_merge_sides
    f = tmp_path / "test.txt"
    f.write_text("local content")
    base, source, dest = get_merge_sides(f, tmp_path)
    assert base == ""
    assert source == ""
    assert dest == "local content"


def test_get_merge_sides_missing_file_returns_empty_dest(tmp_path):
    from biome_fm.plastic._diff import get_merge_sides
    f = tmp_path / "gone.txt"  # does not exist
    base, source, dest = get_merge_sides(f, tmp_path)
    assert base == source == dest == ""


def test_get_merge_sides_error_returns_empty(tmp_path):
    from biome_fm.plastic._diff import get_merge_sides
    f = tmp_path / "gone.txt"
    base, source, dest = get_merge_sides(f, tmp_path)
    assert base == source == dest == ""
