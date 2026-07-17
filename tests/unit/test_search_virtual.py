"""Unit tests for SearchCoordinator.on_search_completed → navigate_virtual wiring."""
from __future__ import annotations

from pathlib import Path

from biome_fm.presenters.search_coordinator import SearchCoordinator
from biome_fm.presenters.search_presenter import SearchResult
from biome_fm.models.file_item import FileItem


def _make_result(name: str = "foo.txt", is_dir: bool = False) -> SearchResult:
    p = Path("/tmp") / name
    return SearchResult(item=FileItem(name=name, path=p, is_dir=is_dir, size=0, modified=0.0))


class _FakePanel:
    def __init__(self) -> None:
        self.result_count = 0
        self._results: list = []

    def add_results(self, r: list) -> None:
        self._results.extend(r)
        self.result_count = len(self._results)

    def on_finished(self, n: int) -> None:
        pass

    def on_cancelled(self) -> None:
        pass

    def on_search_started(self, q: str) -> None:
        pass


def _make_sc(panel=None, on_search_completed=None):
    from biome_fm.views.panel_coordinator import PanelCoordinator  # noqa: F401
    from biome_fm.presenters.manager_presenter import ManagerPresenter  # noqa: F401

    class _FakeVFS:
        pass

    class _FakeCoord:
        def toggle(self, *a) -> None:
            pass

    class _FakeManager:
        active_pane_id = "left"

    class _FakeTabs:
        current_path = Path("/tmp")
        active_idx = 0

        def view_at(self, i: int):
            return None

        def navigate_to(self, p: object) -> None:
            pass

    return SearchCoordinator(
        _FakeVFS(), _FakeCoord(), _FakeManager(),
        panel or _FakePanel(),
        lambda: _FakeTabs(),
        on_search_completed=on_search_completed,
    )


def test_search_completed_calls_navigate_pane():
    """Successful search with results → on_search_completed called with result list."""
    calls: list[list] = []
    sc = _make_sc(on_search_completed=calls.append)
    r = _make_result()
    sc._queue.put(r)
    sc._queue.put(None)  # success sentinel
    sc.drain()
    assert len(calls) == 1
    assert calls[0] == [r]


def test_search_cancelled_does_not_call_navigate():
    """Cancelled search → on_search_completed not called."""
    calls: list = []
    sc = _make_sc(on_search_completed=calls.append)
    sc._queue.put(_make_result())
    sc._queue.put(sc._CANCELLED)
    sc.drain()
    assert calls == []


def test_search_empty_results_does_not_call_navigate():
    """Empty results → on_search_completed not called."""
    calls: list = []
    sc = _make_sc(on_search_completed=calls.append)
    sc._queue.put(None)  # success but no results
    sc.drain()
    assert calls == []


def test_virtual_items_have_correct_paths():
    """Results passed to on_search_completed preserve path/name/is_dir."""
    calls: list[list[SearchResult]] = []
    sc = _make_sc(on_search_completed=calls.append)
    r1 = _make_result("readme.md", is_dir=False)
    r2 = _make_result("src", is_dir=True)
    sc._queue.put(r1)
    sc._queue.put(r2)
    sc._queue.put(None)
    sc.drain()
    assert len(calls) == 1
    results = calls[0]
    assert results[0].item.name == "readme.md"
    assert results[1].item.name == "src"
    assert results[1].item.is_dir is True
