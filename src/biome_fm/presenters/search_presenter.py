"""SearchPresenter — recursive file search, Qt-free."""

from __future__ import annotations

import contextlib
import fnmatch
import re
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


class SearchMode(Enum):
    NAME_WILDCARD = "wildcard"
    NAME_REGEX = "regex"
    CONTENT = "content"


@dataclass(frozen=True, slots=True)
class SearchResult:
    item: FileItem
    context: str = ""


class SearchPresenter:
    """Recursive file search. No Qt. Designed to run in a worker thread."""

    def __init__(self, vfs: VFSProtocol, root: Path) -> None:
        self._vfs = vfs
        self._root = root
        self._cancel = threading.Event()

    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.NAME_WILDCARD,
        max_results: int = 1000,
        on_match: object = None,
        on_progress: object = None,
    ) -> list[SearchResult]:
        """Synchronous recursive search. Call from a worker thread."""
        if not query or max_results <= 0:
            return []
        self._cancel.clear()
        results: list[SearchResult] = []
        with contextlib.suppress(RecursionError):
            self._search_dir(self._root, query, mode, results, max_results, on_match, on_progress)
        return results

    def cancel(self) -> None:
        self._cancel.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    # ------------------------------------------------------------------

    def _search_dir(
        self,
        path: Path,
        query: str,
        mode: SearchMode,
        results: list[SearchResult],
        max_results: int,
        on_match: object = None,
        on_progress: object = None,
    ) -> None:
        if self._cancel.is_set() or len(results) >= max_results:
            return

        if on_progress is not None:
            on_progress(path)  # type: ignore[operator]

        try:
            items = self._vfs.listdir(path)
        except OSError:
            return

        for item in items:
            if self._cancel.is_set() or len(results) >= max_results:
                return

            if item.is_dir:
                if mode != SearchMode.CONTENT:
                    result = self._match(item, query, mode)
                    if result is not None:
                        results.append(result)
                        if on_match is not None:
                            on_match(result)  # type: ignore[operator]
                self._search_dir(
                    item.path, query, mode, results, max_results, on_match, on_progress,
                )
            else:
                result = self._match(item, query, mode)
                if result is not None:
                    results.append(result)
                    if on_match is not None:
                        on_match(result)  # type: ignore[operator]

    def _match(self, item: FileItem, query: str, mode: SearchMode) -> SearchResult | None:
        if mode == SearchMode.NAME_WILDCARD:
            return SearchResult(item=item) if fnmatch.fnmatch(item.name, query) else None

        if mode == SearchMode.NAME_REGEX:
            try:
                return SearchResult(item=item) if re.search(query, item.name) else None
            except re.error:
                return None

        if mode == SearchMode.CONTENT and not item.is_dir:
            return self._content_match(item, query)

        return None

    def _content_match(self, item: FileItem, query: str) -> SearchResult | None:
        try:
            with open(item.path, encoding="utf-8") as fh:
                for line in fh:
                    if query in line:
                        return SearchResult(item=item, context=line.strip()[:200])
        except (UnicodeDecodeError, OSError):
            return None
        return None
