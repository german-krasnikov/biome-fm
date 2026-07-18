"""Tests for content_compare_async — chunked SHA256, cancellable."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from biome_fm.presenters.compare_presenter import content_compare_async


def test_identical_files_returns_true(tmp_path: Path) -> None:
    data = b"hello world" * 100
    (tmp_path / "a").write_bytes(data)
    (tmp_path / "b").write_bytes(data)
    assert content_compare_async(tmp_path / "a", tmp_path / "b", threading.Event()) is True


def test_different_files_returns_false(tmp_path: Path) -> None:
    (tmp_path / "a").write_bytes(b"foo")
    (tmp_path / "b").write_bytes(b"bar")
    assert content_compare_async(tmp_path / "a", tmp_path / "b", threading.Event()) is False


def test_cancel_stops_comparison(tmp_path: Path) -> None:
    """Cancel after first chunk — verifies early exit, not full read."""
    data = b"x" * (300 * 1024)  # 300KB > 256KB chunk
    (tmp_path / "a").write_bytes(data)
    (tmp_path / "b").write_bytes(data)
    cancel = threading.Event()
    calls: list[int] = []

    def progress(done: int, total: int) -> None:
        calls.append(done)
        cancel.set()  # cancel on first progress report

    result = content_compare_async(tmp_path / "a", tmp_path / "b", cancel, progress)
    assert result is False
    assert len(calls) == 1  # stopped after first chunk, not full file


def test_progress_callback_called(tmp_path: Path) -> None:
    """progress(bytes_done, bytes_total) called per chunk."""
    data = b"z" * (512 * 1024)  # 512KB = 2 chunks of 256KB per file
    (tmp_path / "a").write_bytes(data)
    (tmp_path / "b").write_bytes(data)
    cancel = threading.Event()
    calls: list[tuple[int, int]] = []

    result = content_compare_async(
        tmp_path / "a", tmp_path / "b", cancel,
        lambda done, total: calls.append((done, total)),
    )

    assert result is True
    assert len(calls) >= 2  # at least 2 chunks processed
    # bytes_done increases, bytes_total is constant
    totals = {t for _, t in calls}
    assert len(totals) == 1
    dones = [d for d, _ in calls]
    assert dones == sorted(dones)  # monotonically increasing


def test_missing_file_returns_false(tmp_path: Path) -> None:
    (tmp_path / "a").write_bytes(b"data")
    result = content_compare_async(tmp_path / "a", tmp_path / "nope", threading.Event())
    assert result is False


def test_large_files_chunked_hashing(tmp_path: Path) -> None:
    """Files > 1MB are hashed in multiple 256KB chunks."""
    data = b"m" * (2 * 1024 * 1024)  # 2MB
    (tmp_path / "a").write_bytes(data)
    (tmp_path / "b").write_bytes(data)
    cancel = threading.Event()
    calls: list[int] = []

    result = content_compare_async(
        tmp_path / "a", tmp_path / "b", cancel,
        lambda done, _total: calls.append(done),
    )

    assert result is True
    # 2MB / 256KB = 8 chunk pairs (both files read in lockstep)
    assert len(calls) >= 8
