"""SearchCoordinator — concurrent search state machine. No Qt."""
from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from biome_fm.models.vfs import VFSProtocol
    from biome_fm.presenters.tabs_presenter import TabsPresenter
    from biome_fm.views.panel_coordinator import PanelCoordinator
    from biome_fm.views.search_panel import SearchResultsPanel
    from biome_fm.presenters.manager_presenter import ManagerPresenter
    from biome_fm.presenters.search_presenter import SearchResult


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
    ) -> None:
        self._vfs = vfs
        self._coord = coord
        self._manager = manager
        self._panel = panel
        self._get_active = get_active
        self._window = window
        self._presenter = None
        self._queue: queue.SimpleQueue = queue.SimpleQueue()

    def request_search(self) -> None:
        """Show search dialog, cancel any in-progress, start thread. Call on main thread."""
        from biome_fm.presenters.search_presenter import SearchPresenter
        from biome_fm.views.search_dialog import SearchDialog

        if self._presenter is not None:
            self._presenter.cancel()
        self._queue = queue.SimpleQueue()
        active = self._get_active()
        params = SearchDialog.get_params(active.current_path, self._window)  # type: ignore[arg-type]
        if params is None:
            return
        query, mode, max_results = params
        self._presenter = SearchPresenter(self._vfs, active.current_path)
        self._panel.on_search_started(query)
        self._coord.toggle("search", self._manager.active_pane_id)
        q = self._queue

        def _run() -> None:
            self._presenter.search(  # type: ignore[union-attr]
                query, mode=mode, max_results=max_results,
                on_match=q.put,
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
            self._panel.add_results(batch)
        if done:
            if cancelled:
                self._panel.on_cancelled()
            else:
                self._panel.on_finished(self._panel.result_count)

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
