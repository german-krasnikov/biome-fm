"""Unit tests for duplicate file finder (pure Python, no Qt)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.presenters.duplicate_presenter import DupGroup, _file_hash, find_duplicates


def _write(p: Path, content: bytes) -> Path:
    p.write_bytes(content)
    return p


def test_identical_files_grouped(tmp_path):
    content = b"hello world"
    _write(tmp_path / "a.txt", content)
    _write(tmp_path / "b.txt", content)
    groups = find_duplicates(tmp_path, [False])
    assert len(groups) == 1
    assert len(groups[0].paths) == 2
    assert groups[0].size == len(content)


def test_no_duplicates_empty(tmp_path):
    _write(tmp_path / "a.txt", b"aaa")
    _write(tmp_path / "b.txt", b"bbb")
    assert find_duplicates(tmp_path, [False]) == []


def test_cancel_returns_empty(tmp_path):
    _write(tmp_path / "a.txt", b"x")
    _write(tmp_path / "b.txt", b"x")
    assert find_duplicates(tmp_path, [True]) == []


def test_different_content_not_grouped(tmp_path):
    _write(tmp_path / "a.txt", b"foo")
    _write(tmp_path / "b.txt", b"bar")
    assert find_duplicates(tmp_path, [False]) == []


def test_file_hash_consistent(tmp_path):
    p = _write(tmp_path / "f.txt", b"consistent")
    assert _file_hash(p) == _file_hash(p)
    assert _file_hash(p) is not None


def test_size_filter_skips_different_sizes(tmp_path):
    """Files with different sizes must not end up in a group."""
    _write(tmp_path / "a.txt", b"short")
    _write(tmp_path / "b.txt", b"longer content")
    assert find_duplicates(tmp_path, [False]) == []


def test_three_identical_files_one_group(tmp_path):
    content = b"same"
    for name in ("x.txt", "y.txt", "z.txt"):
        _write(tmp_path / name, content)
    groups = find_duplicates(tmp_path, [False])
    assert len(groups) == 1
    assert len(groups[0].paths) == 3
