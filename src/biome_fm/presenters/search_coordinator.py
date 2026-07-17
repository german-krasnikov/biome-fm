"""SearchCoordinator — concurrent search state machine. No Qt."""
from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

_HISTORY_MAX = 30


def add_to_history(history: list[str], query: str) -> list[str]:
    """Return new history list with query at front, deduped, max 30."""
    deduped = [q for q in history if q != query]
    return [query, *deduped][:_HISTORY_MAX]

if TYPE_CHECKING:
    from biome_fm.models.vfs import VFSProtocol
    from biome_fm.presenters.manager_presenter import ManagerPresenter
    from biome_fm.presenters.search_presenter import SearchResult
    from biome_fm.presenters.tabs_presenter import TabsPresenter
    from biome_fm.views.panel_coordinator import PanelCoordinator
    from biome_fm.views.search_panel import SearchResultsPanel


class SearchCoordinator:
    """Manages concurrent search: dialog, thread, queue, drain, cancel."""

    _CANCELLED = object()  # sentinel

    def __init__(
        self,
        vfs: VFSProtocol,
        coord: PanelCoordinator,
        manager: ManagerPresenter,
        panel: SearchResultsPanel,
        get_active: Callable[[], TabsPresenter],
        window: object = None,
        on_search_completed: Callable[[list], None] | None = None,
        store: object = None,
        history: list[str] | None = None,
        on_history_update: Callable[[list[str]], None] | None = None,
    ) -> None:
        self._vfs = vfs
        self._coord = coord
        self._manager = manager
        self._panel = panel
        self._get_active = get_active
        self._window = window
        self._on_search_completed = on_search_completed
        self._store = store
        self._history: list[str] = history if history is not None else []
        self._on_history_update = on_history_update
        self._presenter = None
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._all_results: list = []

    def request_search(self) -> None:
        """Show search dialog, cancel any in-progress, start thread. Call on main thread."""
        from biome_fm.presenters.search_presenter import SearchPresenter
        from biome_fm.views.search_dialog import SearchDialog

        if self._presenter is not None:
            self._presenter.cancel()
        self._queue = queue.SimpleQueue()
        self._all_results = []
        active = self._get_active()
        params = SearchDialog.get_params(
            active.current_path, self._window,  # type: ignore[arg-type]
            store=self._store, history=self._history,
        )
        if params is None:
            return
        query, mode, max_results, scope, filt = params
        self._history = add_to_history(self._history, query)
        if self._on_history_update is not None:
            self._on_history_update(self._history)
        self._presenter = SearchPresenter(self._vfs, active.current_path)
        self._panel.on_search_started(query)
        self._coord.toggle("search", self._manager.active_pane_id)
        q = self._queue

        def _run() -> None:
            self._presenter.search(  # type: ignore[union-attr]
                query, mode=mode, max_results=max_results,
                on_match=q.put, scope=scope, filter=filt,
            )
            sentinel = self._CANCELLED if self._presenter._cancel.is_set() else None  # type: ignore[union-attr]
            q.put(sentinel)

        threading.Thread(target=_run, daemon=True).start()

    def drain(self) -> None:
        """Drain result queue. Called by QTimer on main thread (50ms interval)."""
        batch: list[SearchResult] = []
        done = False
        cancelled = False
        try:
            while True:
                item = self._queue.get_nowait()
                if item is None:
                    done = True
                    break
                if item is self._CANCELLED:
                    done = True
                    cancelled = True
                    break
                batch.append(item)  # type: ignore[arg-type]
        except queue.Empty:
            pass
        if batch:
            self._all_results.extend(batch)
            self._panel.add_results(batch)
        if done:
            if cancelled:
                self._panel.on_cancelled()
            else:
                self._panel.on_finished(self._panel.result_count)
                if self._all_results and self._on_search_completed is not None:
                    self._on_search_completed(list(self._all_results))

    def cancel(self) -> None:
        if self._presenter is not None:
            self._presenter.cancel()

    def navigate_to(self, parent_dir: object, filename: str) -> None:
        """Navigate active pane to a search result. Wired to panel.navigate_to_file."""
        tabs = self._get_active()
        tabs.navigate_to(parent_dir)  # type: ignore[arg-type]
        v = tabs.view_at(tabs.active_idx)
        if hasattr(v, "select_item"):
            v.select_item(filename)  # type: ignore[union-attr]
