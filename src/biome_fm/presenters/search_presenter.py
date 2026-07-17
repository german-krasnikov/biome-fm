"""SearchPresenter — recursive file search, Qt-free."""

from __future__ import annotations

import contextlib
import fnmatch
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


class SearchMode(Enum):
    NAME_WILDCARD = "wildcard"
    NAME_REGEX = "regex"
    CONTENT = "content"
    CONTENT_REGEX = "content_regex"


class SearchScope(Enum):
    SUBTREE = "subtree"
    CURRENT_DIR = "current_dir"


@dataclass(frozen=True, slots=True)
class SearchFilter:
    min_size: int | None = None
    max_size: int | None = None
    modified_after: float | None = None
    modified_before: float | None = None
    extensions: frozenset[str] = field(default_factory=frozenset)

    def passes(self, item: FileItem) -> bool:
        if item.is_dir:
            return True  # never filter directories by size/ext
        if self.min_size is not None and item.size < self.min_size:
            return False
        if self.max_size is not None and item.size > self.max_size:
            return False
        if self.modified_after is not None and item.modified < self.modified_after:
            return False
        if self.modified_before is not None and item.modified > self.modified_before:
            return False
        if self.extensions and Path(item.name).suffix not in self.extensions:
            return False
        return True


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
        scope: SearchScope = SearchScope.SUBTREE,
        filter: SearchFilter | None = None,
    ) -> list[SearchResult]:
        """Synchronous recursive search. Call from a worker thread."""
        if not query or max_results <= 0:
            return []
        self._cancel.clear()
        results: list[SearchResult] = []
        with contextlib.suppress(RecursionError):
            self._search_dir(
                self._root, query, mode, results, max_results,
                on_match, on_progress, scope, filter,
            )
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
        scope: SearchScope = SearchScope.SUBTREE,
        filt: SearchFilter | None = None,
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
                if mode not in (SearchMode.CONTENT, SearchMode.CONTENT_REGEX):
                    result = self._match(item, query, mode)
                    if result is not None:
                        results.append(result)
                        if on_match is not None:
                            on_match(result)  # type: ignore[operator]
                if scope == SearchScope.SUBTREE:
                    self._search_dir(
                        item.path, query, mode, results, max_results,
                        on_match, on_progress, scope, filt,
                    )
            else:
                if filt is not None and not filt.passes(item):
                    continue
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

        if mode == SearchMode.CONTENT_REGEX and not item.is_dir:
            return self._content_regex_match(item, query)

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

    def _content_regex_match(self, item: FileItem, query: str) -> SearchResult | None:
        try:
            pattern = re.compile(query)
        except re.error:
            return None
        try:
            with open(item.path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if pattern.search(line):
                        return SearchResult(
                            item=item,
                            context=f":{lineno}: {line.strip()[:200]}",
                        )
        except (UnicodeDecodeError, OSError):
            return None
        return None
