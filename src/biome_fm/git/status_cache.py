from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RepoStatus:
    statuses: dict[Path, str]       # absolute path → 2-char XY code
    dirty_dirs: frozenset[Path]     # dirs containing dirty files (rollup)
    fetched_at: float               # time.monotonic()


class GitStatusCache:
    TTL: float = 10.0

    def __init__(self) -> None:
        self._cache: dict[Path, RepoStatus] = {}
        self._lock = threading.Lock()
        self._no_repo: set[Path] = set()

    def find_repo(self, path: Path) -> Path | None:
        """Walk up from path looking for .git. Cache negative results."""
        cur = path.resolve()
        while True:
            if cur in self._no_repo:
                return None
            if (cur / ".git").exists():
                return cur
            parent = cur.parent
            if parent == cur:
                self._no_repo.add(path.resolve())
                return None
            cur = parent

    def get_status(self, repo_root: Path) -> RepoStatus:
        """Return cached status if fresh, otherwise fetch."""
        with self._lock:
            cached = self._cache.get(repo_root)
            if cached and (time.monotonic() - cached.fetched_at) < self.TTL:
                return cached
        status = self._fetch(repo_root)
        with self._lock:
            self._cache[repo_root] = status
        return status

    def file_status(self, file_path: Path) -> str | None:
        """Get XY status code for a file. None if no repo or file is clean."""
        repo = self.find_repo(file_path.parent)
        if repo is None:
            return None
        status = self.get_status(repo)
        return status.statuses.get(file_path.resolve())

    def dir_is_dirty(self, dir_path: Path) -> bool:
        repo = self.find_repo(dir_path)
        if repo is None:
            return False
        status = self.get_status(repo)
        return dir_path.resolve() in status.dirty_dirs

    def invalidate(self, repo_root: Path) -> None:
        with self._lock:
            self._cache.pop(repo_root, None)

    def _fetch(self, repo_root: Path) -> RepoStatus:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repo_root, capture_output=True, text=True, timeout=5,
            )
            return self._parse(result.stdout, repo_root)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return RepoStatus({}, frozenset(), time.monotonic())

    @staticmethod
    def _parse(output: str, repo_root: Path) -> RepoStatus:
        statuses: dict[Path, str] = {}
        dirty_dirs: set[Path] = set()
        repo_resolved = repo_root.resolve()
        for line in output.splitlines():
            if len(line) < 4:
                continue
            xy = line[:2]
            rel = line[3:]
            if " -> " in rel:
                rel = rel.split(" -> ", 1)[1]
            abs_path = (repo_root / rel).resolve()
            statuses[abs_path] = xy
            cur = abs_path.parent
            while cur != repo_resolved and cur != cur.parent:
                dirty_dirs.add(cur)
                cur = cur.parent
        return RepoStatus(statuses, frozenset(dirty_dirs), time.monotonic())
