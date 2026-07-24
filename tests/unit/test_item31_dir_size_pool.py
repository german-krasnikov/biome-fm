"""Item #31 — bounded thread pool for dir size calculation."""
from __future__ import annotations

import queue
import time
import threading
from concurrent.futures import wait
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeView:
    def set_items(self, items, **kw): pass
    def set_path(self, p): pass
    def show_error(self, m): pass
    def set_status(self, t): pass
    def set_marked(self, s): pass
    def current_cursor_item(self): return None
    def advance_cursor(self): pass
    def retreat_cursor(self): pass
    def set_filter_visible(self, v): pass
    def set_nav_history(self, h): pass
    def select_item(self, n): pass
    def set_dir_size(self, p, s): pass


# ---------------------------------------------------------------------------
# Scenario 1 — pool exists and is bounded
# ---------------------------------------------------------------------------

def test_pool_is_bounded():
    from biome_fm.utils.dir_size import _POOL
    assert _POOL._max_workers <= 8


def test_pool_thread_count_stays_bounded():
    from biome_fm.utils.dir_size import _POOL
    before = {t.name for t in threading.enumerate()}
    futures = [_POOL.submit(lambda: None) for _ in range(200)]
    wait(futures)
    after = {t.name for t in threading.enumerate()}
    new_dir_size = [n for n in (after - before) if "dir-size" in n]
    assert len(new_dir_size) <= _POOL._max_workers


# ---------------------------------------------------------------------------
# Scenario 2 — results still arrive via queue
# ---------------------------------------------------------------------------

def test_all_dir_sizes_queued(tmp_path):
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.file_item import FileItem
    from biome_fm.models.vfs import LocalVFS

    dirs = []
    for i in range(5):
        d = tmp_path / f"d{i}"
        d.mkdir()
        (d / "f.txt").write_bytes(b"x" * (i + 1))
        dirs.append(FileItem(name=d.name, path=d, is_dir=True, size=0, modified=0.0))

    p = PanePresenter(FakeView(), LocalVFS())
    p._items = dirs
    p.calculate_all_dir_sizes()

    collected: dict[Path, int] = {}
    deadline = time.time() + 3
    while len(collected) < 5 and time.time() < deadline:
        try:
            path, size = p._size_queue.get(timeout=0.1)
            collected[path] = size
        except queue.Empty:
            pass

    assert len(collected) == 5
    assert all(s >= 0 for s in collected.values())


# ---------------------------------------------------------------------------
# Scenario 3 — cancel propagates
# ---------------------------------------------------------------------------

def test_cancel_stops_work(tmp_path):
    from biome_fm.presenters.pane_presenter import PanePresenter
    from biome_fm.models.file_item import FileItem
    from biome_fm.models.vfs import LocalVFS

    dirs = []
    for i in range(5):
        d = tmp_path / f"big{i}"
        d.mkdir()
        # create enough files that walking takes non-zero time
        for j in range(20):
            (d / f"f{j}.txt").write_bytes(b"x" * 1024)
        dirs.append(FileItem(name=d.name, path=d, is_dir=True, size=0, modified=0.0))

    p = PanePresenter(FakeView(), LocalVFS())
    p._items = dirs
    p.calculate_all_dir_sizes()
    p._size_cancel[0] = True  # cancel immediately

    time.sleep(0.3)
    results = []
    while not p._size_queue.empty():
        results.append(p._size_queue.get_nowait())
    # not all 5 should have completed (at most a couple may have snuck through)
    assert len(results) <= 4
