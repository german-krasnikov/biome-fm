"""I2: SearchCoordinator — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from biome_fm.presenters.search_coordinator import SearchCoordinator


class _FakeVFS:
    pass


class _FakeCoord:
    def toggle(self, *a) -> None:
        pass


class _FakeManager:
    active_pane_id = "left"


class _FakePanel:
    def __init__(self) -> None:
        self.results: list = []
        self.finished: int | None = None
        self.cancelled = False
        self.last_query: str | None = None
        self.result_count = 0

    def on_search_started(self, query: str) -> None:
        self.last_query = query

    def add_results(self, r: list) -> None:
        self.results.extend(r)
        self.result_count = len(self.results)

    def on_finished(self, n: int) -> None:
        self.finished = n

    def on_cancelled(self) -> None:
        self.cancelled = True


class _FakeTabs:
    current_path = Path("/tmp")
    active_idx = 0

    def view_at(self, i: int) -> None:
        return None

    def navigate_to(self, p: object) -> None:
        self.nav = p


def _make_sc(panel=None):
    return SearchCoordinator(
        _FakeVFS(), _FakeCoord(), _FakeManager(),
        panel or _FakePanel(),
        lambda: _FakeTabs(),
    )


def test_cancel_before_start_does_not_raise():
    """cancel() before any search must not raise."""
    sc = _make_sc()
    sc.cancel()  # must not raise


def test_drain_empty_does_not_raise():
    """drain() on empty queue must not raise."""
    sc = _make_sc()
    sc.drain()  # must not raise


def test_drain_none_sentinel_fires_on_finished():
    """None sentinel in queue → on_finished is called."""
    panel = _FakePanel()
    sc = _make_sc(panel)
    sc._queue.put(None)
    sc.drain()
    assert panel.finished == 0


def test_drain_cancelled_sentinel_fires_on_cancelled():
    """_CANCELLED sentinel in queue → on_cancelled is called."""
    panel = _FakePanel()
    sc = _make_sc(panel)
    sc._queue.put(sc._CANCELLED)
    sc.drain()
    assert panel.cancelled
