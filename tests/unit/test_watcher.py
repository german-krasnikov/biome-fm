"""Unit tests for WatchService and _Debouncer. No filesystem I/O from watchfiles."""
from __future__ import annotations

import time
from pathlib import Path

from biome_fm.utils.watcher import WatchService, _Debouncer

# ── Fake watch helpers ────────────────────────────────────────────────────────

def _make_fake_watch(*batches):
    """Generator watch fn: yields predefined batches then returns."""
    def _fn(path, stop_event=None, **kwargs):
        for b in batches:
            if stop_event and stop_event.is_set():
                return
            yield b
    return _fn


def _blocking_watch(path, stop_event=None, **kwargs):
    """Generator that blocks until stop_event is set, yielding nothing."""
    if stop_event:
        stop_event.wait(timeout=10.0)
    if False:  # makes it a generator
        yield


# ── _Debouncer ────────────────────────────────────────────────────────────────

def test_debounce_collapses_rapid_events():
    called = []
    d = _Debouncer(lambda: called.append(1), delay=0.02)
    for _ in range(5):
        d.trigger()
    time.sleep(0.08)  # debounce window (20ms) + margin
    assert called == [1]


# ── WatchService ──────────────────────────────────────────────────────────────

def test_watcher_calls_callback_on_change(tmp_path):
    called = []
    svc = WatchService(
        callback=called.append,
        debounce_ms=10,
        _watch_fn=_make_fake_watch({"fake_change"}),
    )
    svc.start(tmp_path)
    svc._thread.join(timeout=1.0)  # fake is finite, thread exits quickly
    time.sleep(0.05)  # wait for debounce timer (10ms) to fire
    assert called == [tmp_path]


def test_stop_cancels_thread(tmp_path):
    svc = WatchService(callback=lambda p: None, _watch_fn=_blocking_watch)
    svc.start(tmp_path)
    time.sleep(0.02)  # let thread actually start
    assert svc._thread is not None and svc._thread.is_alive()
    svc.stop()
    assert not svc._thread.is_alive()


def test_watching_nonexistent_path_noops():
    watch_called = []
    def _fake(path, **kwargs):
        watch_called.append(path)
        return iter([])

    path = Path("/nonexistent_dir_biome_watch_test_xyz")
    svc = WatchService(callback=lambda p: None, _watch_fn=_fake)
    svc.start(path)
    time.sleep(0.05)
    assert watch_called == []
    svc.stop()


def test_set_path_switches_directory(tmp_path):
    watched_paths = []

    def _fake(path, stop_event=None, **kwargs):
        watched_paths.append(path)
        if stop_event:
            stop_event.wait(timeout=5.0)
        if False:
            yield

    dir1 = tmp_path / "a"
    dir1.mkdir()
    dir2 = tmp_path / "b"
    dir2.mkdir()

    svc = WatchService(callback=lambda p: None, _watch_fn=_fake)
    svc.start(dir1)
    time.sleep(0.02)
    svc.set_path(dir2)
    time.sleep(0.02)
    svc.stop()

    assert dir1 in watched_paths
    assert dir2 in watched_paths


def test_import_error_graceful(tmp_path, monkeypatch):
    import biome_fm.utils.watcher as wmod
    monkeypatch.setattr(wmod, "_WATCH_FN", None)
    svc = WatchService(callback=lambda p: None)  # no _watch_fn, module-level also None
    svc.start(tmp_path)
    assert svc._thread is None  # no thread started
