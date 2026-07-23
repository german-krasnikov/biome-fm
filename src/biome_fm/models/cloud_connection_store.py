"""F303 — Simple JSON store for cloud connection URLs."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models._store_base import atomic_write_json, read_json


class CloudConnectionStore:
    """Persist a list of cloud URLs (s3://, ftp://, etc.) to JSON."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._urls: list[str] = []

    def load(self) -> None:
        self._urls = read_json(self._path, default=[])

    def save(self) -> None:
        atomic_write_json(self._path, self._urls)

    def add(self, url: str) -> None:
        if url not in self._urls:
            self._urls.append(url)

    def remove(self, url: str) -> None:
        self._urls = [u for u in self._urls if u != url]

    def list(self) -> list[str]:
        return list(self._urls)
