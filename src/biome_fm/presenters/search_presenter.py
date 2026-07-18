"""SearchPresenter — recursive file search, Qt-free."""

from __future__ import annotations

import contextlib
import fnmatch
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import VFSProtocol


DEFAULT_EXCLUDE = [
    ".git", "node_modules", "__pycache__", ".venv", "venv", "vendor",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".idea", ".vscode",
]


class SearchMode(Enum):
    NAME_WILDCARD = "wildcard"
    NAME_REGEX = "regex"
    CONTENT = "content"
    CONTENT_REGEX = "content_regex"


class SearchScope(Enum):
    SUBTREE = "subtree"
    CURRENT_DIR = "current_dir"
    SELECTED_FILES = "selected"
    BOTH_PANES = "both_panes"


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


def _decode_content(raw: bytes) -> str | None:
    """Decode raw bytes to str, or None if likely binary.

    Chain: UTF-8 → chardet (optional) → latin-1 fallback.
    Returns None when >30% of first 8 KB are non-printable control bytes.
    """
    if not raw:
        return ""
    sample = raw[:8192]
    non_printable = sum(1 for b in sample if b < 9 or 13 < b < 32 or b == 127)
    if non_printable / len(sample) > 0.30:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        import chardet  # optional dependency
        enc = (chardet.detect(sample) or {}).get("encoding")
        if enc:
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                pass
    except ImportError:
        pass
    return raw.decode("latin-1")  # never raises


class SearchPresenter:
    """Recursive file search. No Qt. Designed to run in a worker thread."""

    def __init__(self, vfs: VFSProtocol, root: Path) -> None:
        self._vfs = vfs
        self._root = root
        self._cancel = threading.Event()
        self._case_sensitive = False
        self._whole_word = False
        self._context_lines: int = 0

    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.NAME_WILDCARD,
        max_results: int = 1000,
        on_match: object = None,
        on_progress: object = None,
        scope: SearchScope = SearchScope.SUBTREE,
        filter: SearchFilter | None = None,
        exclude_patterns: list[str] | None = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        context_lines: int = 0,
    ) -> list[SearchResult]:
        """Synchronous recursive search. Call from a worker thread."""
        if not query or max_results <= 0:
            return []
        self._case_sensitive = case_sensitive
        self._whole_word = whole_word
        self._context_lines = context_lines
        self._cancel.clear()
        excl = DEFAULT_EXCLUDE if exclude_patterns is None else exclude_patterns
        results: list[SearchResult] = []
        with contextlib.suppress(RecursionError):
            self._search_dir(
                self._root, query, mode, results, max_results,
                on_match, on_progress, scope, filter, excl,
            )
        return results

    def cancel(self) -> None:
        self._cancel.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    def match_item(
        self,
        item: FileItem,
        query: str,
        mode: SearchMode = SearchMode.NAME_WILDCARD,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
        context_lines: int = 0,
    ) -> SearchResult | None:
        """Match a single FileItem against query. Used by SELECTED_FILES scope."""
        self._case_sensitive = case_sensitive
        self._whole_word = whole_word
        self._context_lines = context_lines
        return self._match(item, query, mode)

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
        exclude_patterns: list[str] | None = None,
    ) -> None:
        if self._cancel.is_set() or len(results) >= max_results:
            return

        if on_progress is not None:
            on_progress(path)  # type: ignore[operator]

        try:
            items = self._vfs.listdir(path)
        except OSError:
            return

        excl = exclude_patterns or []
        dir_items: list = []
        file_items: list = []
        for item in items:
            if item.is_dir:
                if not (excl and any(fnmatch.fnmatch(item.name, p) for p in excl)):
                    dir_items.append(item)
            else:
                if filt is None or filt.passes(item):
                    file_items.append(item)

        # Parallel for I/O-bound content reads; serial for name-only modes (fast, no I/O)
        if mode in (SearchMode.CONTENT, SearchMode.CONTENT_REGEX) and file_items:
            self._process_files_parallel(file_items, query, mode, results, max_results, on_match)
        else:
            for item in file_items:
                if self._cancel.is_set() or len(results) >= max_results:
                    return
                result = self._match(item, query, mode)
                if result is not None:
                    results.append(result)
                    if on_match is not None:
                        on_match(result)  # type: ignore[operator]

        for item in dir_items:
            if self._cancel.is_set() or len(results) >= max_results:
                return
            if mode not in (SearchMode.CONTENT, SearchMode.CONTENT_REGEX):
                result = self._match(item, query, mode)
                if result is not None:
                    results.append(result)
                    if on_match is not None:
                        on_match(result)  # type: ignore[operator]
            if scope == SearchScope.SUBTREE:
                self._search_dir(
                    item.path, query, mode, results, max_results,
                    on_match, on_progress, scope, filt, excl,
                )

    def _process_files_parallel(
        self,
        file_items: list,
        query: str,
        mode: SearchMode,
        results: list[SearchResult],
        max_results: int,
        on_match: object,
    ) -> None:
        # ponytail: GIL limits CPU-bound; cpu//2 avoids starving Qt event loop
        workers = min(max(1, (os.cpu_count() or 2) // 2), 4)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._match, item, query, mode): item for item in file_items}
            for future in as_completed(futures):
                if self._cancel.is_set() or len(results) >= max_results:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    result = future.result()
                except Exception:
                    continue
                if result is not None:
                    results.append(result)
                    if on_match is not None:
                        on_match(result)  # type: ignore[operator]

    def _match(self, item: FileItem, query: str, mode: SearchMode) -> SearchResult | None:
        if mode == SearchMode.NAME_WILDCARD:
            # Normalise cross-platform: fnmatch is case-insensitive on macOS, sensitive on Linux
            # Semicolon separates multiple patterns (TC/Far/DC convention)
            patterns = [p.strip() for p in query.split(";") if p.strip()]
            matched = (
                any(fnmatch.fnmatchcase(item.name, p) for p in patterns)
                if self._case_sensitive
                else any(fnmatch.fnmatch(item.name.lower(), p.lower()) for p in patterns)
            )
            return SearchResult(item=item) if matched else None

        if mode == SearchMode.NAME_REGEX:
            try:
                flags = 0 if self._case_sensitive else re.IGNORECASE
                pat = (r'\b(?:' + query + r')\b') if self._whole_word else query
                return SearchResult(item=item) if re.search(pat, item.name, flags) else None
            except re.error:
                return None

        if mode == SearchMode.CONTENT and not item.is_dir:
            return self._content_match(item, query)

        if mode == SearchMode.CONTENT_REGEX and not item.is_dir:
            return self._content_regex_match(item, query)

        return None

    def _content_match(self, item: FileItem, query: str) -> SearchResult | None:
        if item.size > 50 * 1024 * 1024:  # ponytail: peak RSS ~3× (bytes+str+splitlines); lower to 16MB or mmap if memory matters
            return None
        try:
            raw = self._vfs.read_bytes(item.path)
            if not isinstance(raw, (bytes, bytearray)):
                raw = item.path.read_bytes()
        except OSError:
            return None
        text = _decode_content(raw)
        if text is None:
            return None
        flags = 0 if self._case_sensitive else re.IGNORECASE
        pattern = (r'\b' + re.escape(query) + r'\b') if self._whole_word else re.escape(query)
        rx = re.compile(pattern, flags)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if rx.search(line):
                ctx = lines[max(0, i - self._context_lines) : i + self._context_lines + 1]
                return SearchResult(item=item, context="\n".join(ctx)[:200])
        return None

    def _content_regex_match(self, item: FileItem, query: str) -> SearchResult | None:
        try:
            flags = 0 if self._case_sensitive else re.IGNORECASE
            pat = (r'\b(?:' + query + r')\b') if self._whole_word else query
            pattern = re.compile(pat, flags)
        except re.error:
            return None
        if item.size > 50 * 1024 * 1024:
            return None
        try:
            raw = self._vfs.read_bytes(item.path)
        except OSError:
            return None
        text = _decode_content(raw)
        if text is None:
            return None
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if pattern.search(line):
                ctx = lines[max(0, i - self._context_lines) : i + self._context_lines + 1]
                return SearchResult(item=item, context="\n".join(ctx)[:200])
        return None
