"""F297 — Build a list[FileItem] from git changed files."""
from __future__ import annotations

from pathlib import Path

from biome_fm.git.status_cache import GitStatusCache
from biome_fm.models.file_item import FileItem


def git_changed_files(repo: Path, cache: GitStatusCache) -> list[FileItem]:
    """Return FileItem list for all dirty paths in repo."""
    status = cache.get_status(repo)
    return [
        FileItem(name=p.name, path=p, is_dir=False, size=0, modified=0.0)
        for p in status.statuses
    ]
