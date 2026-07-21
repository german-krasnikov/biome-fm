"""PreviewPresenter — Qt-free. Toggle/update logic, cache, ThreadPool."""
from __future__ import annotations

import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

_CACHE_TTL = 60.0

from biome_fm.models.file_item import FileItem
from biome_fm.preview.provider import ContentKind, PreviewMode, PreviewRequest, PreviewResult
from biome_fm.preview.registry import PreviewRegistry


class _RawProvider:
    """Displays raw bytes as hex/text without sniffing."""
    priority = 999

    def can_handle(self, path: Path) -> bool:
        return True

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            data = req.path.read_bytes()[:4096]
            return PreviewResult(kind=ContentKind.TEXT, data=repr(data), title=req.path.name)
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))


class PreviewViewProtocol(Protocol):
    def show_result(self, result: PreviewResult) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def set_visible(self, visible: bool) -> None: ...
    def is_panel_visible(self) -> bool: ...
    def scroll_to_bottom(self) -> None: ...


class PreviewPresenter:
    _CACHE_MAX = 64

    def __init__(self, view: PreviewViewProtocol, registry: PreviewRegistry) -> None:
        self._view = view
        self._registry = registry
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="preview")
        self._queue: queue.SimpleQueue[PreviewResult] = queue.SimpleQueue()
        self._current: Path | None = None
        self._cache: dict[tuple[Path, float, bool], tuple[PreviewResult, float]] = {}
        self._cache_lock = threading.Lock()
        self._dark = True  # theme hint; updated via set_dark()
        self._forced_mode: PreviewMode = PreviewMode.AUTO
        self._tail_mode: bool = False

    def set_dark(self, dark: bool) -> None:
        self._dark = dark

    def set_tail_mode(self, enabled: bool) -> None:
        self._tail_mode = enabled

    def set_mode(self, mode: PreviewMode) -> None:
        self._forced_mode = mode
        if self._current is not None:
            item = FileItem(
                name=self._current.name,
                path=self._current,
                is_dir=False, size=0, modified=0.0,
            )
            self._render_item(item)

    def _auto_detect_mode(self, item: FileItem) -> str:
        """Return 'hex' for binary files, 'text' otherwise. Pure function, no Qt."""
        if item.is_dir or item.size == 0:
            return "text"
        try:
            sample = item.path.read_bytes()[:512]
        except OSError:
            return "text"
        if not sample:
            return "text"
        non_print = sum(1 for b in sample if b < 9 or 13 < b < 32 or b == 127)
        return "hex" if non_print / len(sample) > 0.30 else "text"

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
            entry = self._cache.get(cache_key)
            hit = entry[0] if entry and (time.monotonic() - entry[1]) < _CACHE_TTL else None
        if hit is not None:
            self._view.show_result(hit)
            return
        self._view.set_busy(True)
        provider = self._get_provider(item.path, item)
        req = PreviewRequest(path=item.path, dark=self._dark)
        self._pool.submit(self._run, provider, req, cache_key)

    def _get_provider(self, path: Path, item: FileItem | None = None):
        match self._forced_mode:
            case PreviewMode.TEXT:
                from biome_fm.preview.providers.text import TextPreviewProvider
                return TextPreviewProvider()
            case PreviewMode.HEX:
                from biome_fm.preview.providers.hex import HexPreviewProvider
                return HexPreviewProvider()
            case PreviewMode.RAW:
                return _RawProvider()
            case PreviewMode.GIT_LOG:
                from biome_fm.preview.providers.git_log import GitLogPreviewProvider
                return GitLogPreviewProvider()
            case PreviewMode.GIT_BLAME:
                from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
                return GitBlamePreviewProvider()
            case _:
                # Auto-detect binary files → hex; don't override explicit user selection
                if item is not None and self._auto_detect_mode(item) == "hex":
                    from biome_fm.preview.providers.hex import HexPreviewProvider
                    return HexPreviewProvider()
                return self._registry.find(path)

    def _run(self, provider, req: PreviewRequest, cache_key: tuple[Path, float, bool]) -> None:
        """Background thread — must not touch Qt."""
        try:
            result = provider.render(req)
        except Exception as e:
            result = PreviewResult(kind=ContentKind.ERROR, data=str(e))
        with self._cache_lock:
            if len(self._cache) >= self._CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = (result, time.monotonic())
        if req.path == self._current and req.dark == self._dark:
            self._queue.put(result)

    def drain(self) -> None:
        """Drain result queue. Called by QTimer in main thread."""
        try:
            while True:
                result = self._queue.get_nowait()
                self._view.set_busy(False)
                self._view.show_result(result)
                if self._tail_mode:
                    self._view.scroll_to_bottom()
        except queue.Empty:
            pass

    def toggle_panel(self) -> None:
        self._view.set_visible(not self._view.is_panel_visible())

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
