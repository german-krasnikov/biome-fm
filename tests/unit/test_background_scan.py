"""Unit tests for _scan_worker — pure Python, no Qt."""

from __future__ import annotations

import queue
import threading
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.directory_model import _scan_worker


def _items(n: int) -> list[FileItem]:
    return [
        FileItem(name=f"file{i}.txt", path=Path(f"/tmp/file{i}.txt"),
                 is_dir=False, size=i, modified=0.0)
        for i in range(n)
    ]


def _drain(q: queue.SimpleQueue) -> tuple[list[FileItem], bool]:
    """Drain queue; return (all_items, got_sentinel)."""
    collected: list[FileItem] = []
    sentinel = False
    while True:
        try:
            chunk = q.get_nowait()
        except queue.Empty:
            break
        if chunk is None:
            sentinel = True
            break
        if isinstance(chunk, list):
            collected.extend(chunk)
    return collected, sentinel


def test_scan_emits_items_via_queue():
    items = _items(100)
    q: queue.SimpleQueue = queue.SimpleQueue()
    _scan_worker(lambda p: items, Path("/tmp"), threading.Event(), q, batch_size=500)
    collected, got_sentinel = _drain(q)
    assert len(collected) == 100
    assert got_sentinel


def test_cancel_stops_scan():
    items = _items(1500)
    q: queue.SimpleQueue = queue.SimpleQueue()
    cancel = threading.Event()
    cancel.set()  # pre-cancelled
    _scan_worker(lambda p: items, Path("/tmp"), cancel, q, batch_size=500)
    assert q.empty()


def test_large_dir_multiple_batches():
    items = _items(1500)
    q: queue.SimpleQueue = queue.SimpleQueue()
    _scan_worker(lambda p: items, Path("/tmp"), threading.Event(), q, batch_size=500)

    chunks: list[list[FileItem]] = []
    while True:
        chunk = q.get_nowait()
        if chunk is None:
            break
        chunks.append(chunk)

    assert len(chunks) == 3  # ceil(1500/500)
    assert sum(len(c) for c in chunks) == 1500


def test_previous_scan_cancelled_on_new_scan():
    """Cancel event from first scan prevents it from emitting batches."""
    items = _items(1000)
    q1: queue.SimpleQueue = queue.SimpleQueue()
    q2: queue.SimpleQueue = queue.SimpleQueue()

    # First scan: cancelled before any batch
    cancel1 = threading.Event()
    cancel1.set()
    _scan_worker(lambda p: items, Path("/tmp"), cancel1, q1, batch_size=500)
    assert q1.empty()

    # Second scan: runs normally
    _scan_worker(lambda p: items, Path("/tmp"), threading.Event(), q2, batch_size=500)
    collected, got_sentinel = _drain(q2)
    assert len(collected) == 1000
    assert got_sentinel


def test_empty_dir_scan():
    q: queue.SimpleQueue = queue.SimpleQueue()
    _scan_worker(lambda p: [], Path("/tmp"), threading.Event(), q, batch_size=500)
    chunk = q.get_nowait()
    assert chunk is None  # only sentinel
    assert q.empty()


def test_oserror_puts_error_string():
    q: queue.SimpleQueue = queue.SimpleQueue()
    _scan_worker(lambda p: (_ for _ in ()).throw(OSError("no access")), Path("/tmp"), threading.Event(), q)
    chunk = q.get_nowait()
    assert isinstance(chunk, str)
    assert "no access" in chunk


def test_non_oserror_puts_error_string():
    q: queue.SimpleQueue = queue.SimpleQueue()
    _scan_worker(lambda p: (_ for _ in ()).throw(RuntimeError("vfs broke")), Path("/tmp"), threading.Event(), q)
    chunk = q.get_nowait()
    assert isinstance(chunk, str)
    assert "vfs broke" in chunk


def test_error_suppressed_when_cancelled():
    q: queue.SimpleQueue = queue.SimpleQueue()
    cancel = threading.Event()
    cancel.set()
    _scan_worker(lambda p: (_ for _ in ()).throw(OSError("no access")), Path("/tmp"), cancel, q)
    assert q.empty()
