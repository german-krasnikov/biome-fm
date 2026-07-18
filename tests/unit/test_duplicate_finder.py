"""Tests for cross-directory duplicate finder (F332)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.presenters.duplicate_presenter import DupGroup, find_duplicates


def _write(p: Path, content: bytes) -> Path:
    p.write_bytes(content)
    return p


def test_find_duplicates_by_hash_cross_dir(tmp_path):
    """Same content in two different subdirectories → one group."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    content = b"duplicate content"
    _write(dir_a / "file.txt", content)
    _write(dir_b / "file.txt", content)
    groups = find_duplicates([dir_a, dir_b], [False])
    assert len(groups) == 1
    assert len(groups[0].paths) == 2


def test_different_content_not_grouped_cross_dir(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    _write(dir_a / "file.txt", b"alpha")
    _write(dir_b / "file.txt", b"beta")
    assert find_duplicates([dir_a, dir_b], [False]) == []


def test_size_prefilter_skips_hashing(tmp_path):
    """Files with different sizes must not appear in any group."""
    _write(tmp_path / "small.txt", b"hi")
    _write(tmp_path / "large.txt", b"hello world")
    groups = find_duplicates([tmp_path], [False])
    assert groups == []


def test_single_path_list_same_as_scalar(tmp_path):
    """find_duplicates([path], ...) works the same as the old (path, ...) call."""
    content = b"same"
    _write(tmp_path / "x.txt", content)
    _write(tmp_path / "y.txt", content)
    groups = find_duplicates([tmp_path], [False])
    assert len(groups) == 1
