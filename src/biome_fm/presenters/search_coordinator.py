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
        self._cancel_flag = threading.Event()

    def request_search(self) -> None:
        """Show search dialog, cancel any in-progress, start thread. Call on main thread."""
        from biome_fm.presenters.search_presenter import SearchPresenter, SearchScope
        from biome_fm.views.search_dialog import SearchDialog

        self._cancel_flag.clear()
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
        query, mode, max_results, scope, filt, exclude_patterns, case_sensitive, whole_word, context_lines = params
        self._history = add_to_history(self._history, query)
        if self._on_history_update is not None:
            self._on_history_update(self._history)
        self._panel.on_search_started(query)
        self._coord.toggle("search", self._manager.active_pane_id)
        q = self._queue

        if scope == SearchScope.SELECTED_FILES:
            marked = active.marked_items  # type: ignore[attr-defined]

            def _run_selected() -> None:
                try:
                    if not marked:
                        return
                    p = SearchPresenter(self._vfs, active.current_path)
                    self._presenter = p
                    for item in marked:
                        if self._cancel_flag.is_set():
                            return
                        result = p.match_item(
                            item, query, mode,
                            case_sensitive=case_sensitive,
                            whole_word=whole_word,
                            context_lines=context_lines,
                        )
                        if result is not None:
                            q.put(result)
                finally:
                    q.put(self._CANCELLED if self._cancel_flag.is_set() else None)

            threading.Thread(target=_run_selected, daemon=True).start()
            return

        if scope == SearchScope.BOTH_PANES:
            inactive_path = self._manager.inactive_pane.current_path  # type: ignore[union-attr]
            roots = list(dict.fromkeys([active.current_path, inactive_path]))

            def _run_both() -> None:
                try:
                    for root in roots:
                        if self._cancel_flag.is_set():
                            return
                        p = SearchPresenter(self._vfs, root)
                        self._presenter = p
                        p.search(
                            query, mode=mode, max_results=max_results,
                            on_match=q.put, scope=SearchScope.SUBTREE, filter=filt,
                            exclude_patterns=exclude_patterns,
                            case_sensitive=case_sensitive, whole_word=whole_word,
                            context_lines=context_lines,
                        )
                        if p.is_cancelled:
                            return
                finally:
                    q.put(self._CANCELLED if self._cancel_flag.is_set() else None)

            threading.Thread(target=_run_both, daemon=True).start()
            return

        # Default: SUBTREE / CURRENT_DIR
        self._presenter = SearchPresenter(self._vfs, active.current_path)

        def _run() -> None:
            try:
                self._presenter.search(  # type: ignore[union-attr]
                    query, mode=mode, max_results=max_results,
                    on_match=q.put, scope=scope, filter=filt,
                    exclude_patterns=exclude_patterns,
                    case_sensitive=case_sensitive, whole_word=whole_word,
                    context_lines=context_lines,
                )
            finally:
                sentinel = self._CANCELLED if self._presenter.is_cancelled else None  # type: ignore[union-attr]
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
        self._cancel_flag.set()
        if self._presenter is not None:
            self._presenter.cancel()

    def navigate_to(self, parent_dir: object, filename: str) -> None:
        """Navigate active pane to a search result. Wired to panel.navigate_to_file."""
        tabs = self._get_active()
        tabs.navigate_to(parent_dir)  # type: ignore[arg-type]
        v = tabs.view_at(tabs.active_idx)
        if hasattr(v, "select_item"):
            v.select_item(filename)  # type: ignore[union-attr]
