"""GitStatusWorker — fetches git status off the main thread."""
from __future__ import annotations

import queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from biome_fm.git.status_cache import GitStatusCache, RepoStatus
from biome_fm.qt import QObject, QTimer, Signal


class GitStatusWorker(QObject):
    status_ready = Signal(object)  # emits RepoStatus

    def __init__(self, cache: GitStatusCache, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cache = cache
        self._pool = ThreadPoolExecutor(max_workers=1)
        self._queue: queue.SimpleQueue[RepoStatus] = queue.SimpleQueue()
        self._pending: Path | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._drain)
        self._timer.start()

        self._head_timer = QTimer(self)
        self._head_timer.setInterval(2000)
        self._head_timer.timeout.connect(self._check_head)

        self._head_path: Path | None = None
        self._head_mtime: float | None = None

    def request(self, dir_path: Path) -> None:
        """Request git status for dir_path. Deduplicates by repo root."""
        repo = self._cache.find_repo(dir_path)
        if repo is None:
            self._head_timer.stop()
            self._head_path = None
            return
        if self._pending == repo:
            return
        self._pending = repo
        self._head_path = repo / ".git" / "HEAD"
        self._head_mtime = None
        self._cache.invalidate(repo)
        self._pool.submit(self._fetch, repo)
        self._head_timer.start()

    def _check_head(self) -> None:
        if self._head_path is None or not self._head_path.exists():
            return
        mtime = self._head_path.stat().st_mtime
        if self._head_mtime is None:
            self._head_mtime = mtime
            return
        if mtime != self._head_mtime:
            self._head_mtime = mtime
            if self._pending is not None:
                self._pool.submit(self._fetch, self._pending)

    def stop(self) -> None:
        self._head_timer.stop()
        self._timer.stop()
        self._pool.shutdown(wait=False)

    def _fetch(self, repo_root: Path) -> None:
        status = self._cache.get_status(repo_root)
        self._queue.put(status)

    def _drain(self) -> None:
        try:
            status = self._queue.get_nowait()
            self._pending = None
            self.status_ready.emit(status)
        except queue.Empty:
            pass
