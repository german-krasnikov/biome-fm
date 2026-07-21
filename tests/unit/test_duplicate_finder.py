"""Tests for cross-directory duplicate finder (F332/F432)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.presenters.duplicate_presenter import DupGroup, _partial_hash, find_duplicates


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


# F432 — partial hash stage tests

def test_partial_hash_reads_only_n_bytes(tmp_path):
    """_partial_hash(p, n) hashes only first n bytes; two files that differ after n bytes share same partial hash."""
    n = 4096
    prefix = b"X" * n
    a = _write(tmp_path / "a.bin", prefix + b"AAAA")
    b_ = _write(tmp_path / "b.bin", prefix + b"BBBB")
    assert _partial_hash(a, n) == _partial_hash(b_, n)


def test_partial_hash_distinguishes_different_prefixes(tmp_path):
    a = _write(tmp_path / "a.bin", b"alpha" + b"\x00" * 100)
    b_ = _write(tmp_path / "b.bin", b"beta" + b"\x00" * 100)
    assert _partial_hash(a) != _partial_hash(b_)


def test_three_same_size_different_content_no_false_positive(tmp_path):
    """3 files same size, all different content → no groups (partial hash must not cause false collisions)."""
    for i, content in enumerate([b"aaa", b"bbb", b"ccc"]):
        _write(tmp_path / f"f{i}.txt", content)
    assert find_duplicates([tmp_path], [False]) == []


def test_cancel_in_partial_hash_stage(tmp_path):
    """cancel[0]=True before partial hash stage → returns []."""
    for i in range(3):
        _write(tmp_path / f"f{i}.txt", b"same content here")
    cancel = [True]
    assert find_duplicates([tmp_path], cancel) == []
