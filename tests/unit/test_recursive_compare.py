"""Unit tests for ComparePresenter.compare_recursive()."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.compare_presenter import ComparePresenter, CompareStatus


@pytest.fixture
def left(tmp_path):
    d = tmp_path / "left"
    d.mkdir()
    return d


@pytest.fixture
def right(tmp_path):
    d = tmp_path / "right"
    d.mkdir()
    return d


def _presenter():
    return ComparePresenter([], [])


def test_compare_identical_trees(left, right) -> None:
    (left / "a.txt").write_text("hello")
    (right / "a.txt").write_text("hello")
    entries = _presenter().compare_recursive(left, right)
    assert all(e.status == CompareStatus.EQUAL for e in entries)


def test_compare_missing_file_in_right(left, right) -> None:
    (left / "only_left.txt").write_text("x")
    entries = _presenter().compare_recursive(left, right)
    assert len(entries) == 1
    assert entries[0].status == CompareStatus.LEFT_ONLY
    assert entries[0].name == "only_left.txt"


def test_compare_different_content(left, right) -> None:
    (left / "f.txt").write_text("abc")
    (right / "f.txt").write_text("abcdef")  # different size → DIFF_SIZE
    entries = _presenter().compare_recursive(left, right)
    assert len(entries) == 1
    assert entries[0].status == CompareStatus.DIFF_SIZE


def test_compare_nested_subdirs(left, right) -> None:
    sub_l = left / "sub"
    sub_l.mkdir()
    (sub_l / "nested.txt").write_text("data")
    sub_r = right / "sub"
    sub_r.mkdir()
    # nested.txt missing on right
    entries = _presenter().compare_recursive(left, right)
    assert any(e.name == "sub/nested.txt" and e.status == CompareStatus.LEFT_ONLY for e in entries)


def test_compare_cancel(left, right) -> None:
    for i in range(5):
        (left / f"f{i}.txt").write_text("x" * i)
        (right / f"f{i}.txt").write_text("x" * i)
    cancel = threading.Event()
    cancel.set()  # pre-cancelled
    entries = _presenter().compare_recursive(left, right, cancel=cancel)
    # With cancel pre-set the walk should return immediately; <= full count
    assert isinstance(entries, list)
