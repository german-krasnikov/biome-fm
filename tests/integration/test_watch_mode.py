"""Integration test: WatchService with real watchfiles detects filesystem changes."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("watchfiles")

from biome_fm.utils.watcher import WatchService


def test_new_file_triggers_callback(tmp_path):
    received: list[Path] = []
    event = threading.Event()

    def _cb(path: Path) -> None:
        received.append(path)
        event.set()

    svc = WatchService(callback=_cb, debounce_ms=200)
    svc.start(tmp_path)
    time.sleep(0.1)  # let watcher thread start

    (tmp_path / "new.txt").write_text("hello")

    fired = event.wait(timeout=5.0)
    svc.stop()

    assert fired, "WatchService callback not fired within 5s after file creation"
    assert received[0] == tmp_path
