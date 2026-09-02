"""Unit tests — nav pool is isolated from dir-size pool (C47)."""

from __future__ import annotations

import threading
from pathlib import Path

from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.pane_presenter import PanePresenter
from tests.unit.test_pane_presenter import FakePaneView


def _saturate_dir_size_pool() -> threading.Event:
    """Block all 4 workers in dir_size._POOL; return event to release them."""
    from biome_fm.utils import dir_size

    release = threading.Event()
    for _ in range(dir_size._POOL._max_workers):
        dir_size._POOL.submit(release.wait)
    return release


def test_nav_completes_while_dir_size_pool_saturated(tmp_path: Path) -> None:
    release = _saturate_dir_size_pool()
    try:
        view = FakePaneView()
        p = PanePresenter(view, LocalVFS())
        p.navigate_to(tmp_path)
        assert p._nav_future is not None
        p._nav_future.result(timeout=2.0)  # must NOT block behind dir-size jobs
        p.drain_nav()
        assert view.path == tmp_path
    finally:
        release.set()


def test_nav_pool_is_bounded() -> None:
    from biome_fm.presenters.pane_presenter import _NAV_POOL

    assert _NAV_POOL._max_workers == 2
