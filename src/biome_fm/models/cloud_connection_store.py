"""F303 — Simple JSON store for cloud connection URLs."""
from __future__ import annotations

import json
from pathlib import Path


class CloudConnectionStore:
    """Persist a list of cloud URLs (s3://, ftp://, etc.) to JSON."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._urls: list[str] = []

    def load(self) -> None:
        if self._path.exists():
            self._urls = json.loads(self._path.read_text())

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._urls))

    def add(self, url: str) -> None:
        if url not in self._urls:
            self._urls.append(url)

    def remove(self, url: str) -> None:
        self._urls = [u for u in self._urls if u != url]

    def list(self) -> list[str]:
        return list(self._urls)
