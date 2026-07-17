"""PreviewPresenter — Qt-free. Toggle/update logic, cache, ThreadPool."""
from __future__ import annotations

import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from biome_fm.models.file_item import FileItem
from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


class PreviewViewProtocol(Protocol):
    def show_result(self, result: PreviewResult) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def set_visible(self, visible: bool) -> None: ...
    def is_panel_visible(self) -> bool: ...


class PreviewPresenter:
    _CACHE_MAX = 64

    def __init__(self, view: PreviewViewProtocol, registry: PreviewRegistry) -> None:
        self._view = view
        self._registry = registry
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="preview")
        self._queue: queue.SimpleQueue[PreviewResult] = queue.SimpleQueue()
        self._current: Path | None = None
        self._cache: dict[tuple[Path, float, bool], PreviewResult] = {}
        self._cache_lock = threading.Lock()
        self._dark = True  # theme hint; updated via set_dark()

    def set_dark(self, dark: bool) -> None:
        self._dark = dark

    def toggle_item(self, item: FileItem | None) -> None:
        if item is None or item.name == "..":
            return
        if not self._view.is_panel_visible():
            self._view.set_visible(True)
            self._render_item(item)
        elif item.path == self._current:
            self._current = None
            self._view.set_visible(False)
        else:
            self._render_item(item)

    def render_item(self, item: FileItem | None) -> None:
        """Render content only — no visibility change."""
        if item is None or item.name == "..":
            return
        self._render_item(item)

    def update_if_visible(self, item: FileItem | None) -> None:
        if not self._view.is_panel_visible():
            return
        if item is None or item.name == ".." or item.path == self._current:
            return
        self._render_item(item)

    def _render_item(self, item: FileItem) -> None:
        self._current = item.path
        cache_key = (item.path, item.modified, self._dark)
        with self._cache_lock:
            hit = self._cache.get(cache_key)
        if hit is not None:
            self._view.show_result(hit)
            return
        self._view.set_busy(True)
        provider = self._registry.find(item.path)
        req = PreviewRequest(path=item.path, dark=self._dark)
        self._pool.submit(self._run, provider, req, cache_key)

    def _run(self, provider, req: PreviewRequest, cache_key: tuple[Path, float, bool]) -> None:
        """Background thread — must not touch Qt."""
        try:
            result = provider.render(req)
        except Exception as e:
            result = PreviewResult(kind=ContentKind.ERROR, data=str(e))
        with self._cache_lock:
            if len(self._cache) >= self._CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = result
        if req.path == self._current and req.dark == self._dark:
            self._queue.put(result)

    def drain(self) -> None:
        """Drain result queue. Called by QTimer in main thread."""
        try:
            while True:
                result = self._queue.get_nowait()
                self._view.set_busy(False)
                self._view.show_result(result)
        except queue.Empty:
            pass

    def toggle_panel(self) -> None:
        self._view.set_visible(not self._view.is_panel_visible())

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
