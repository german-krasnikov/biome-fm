from __future__ import annotations
from pathlib import Path


class Hotlist:
    def __init__(self, store) -> None:
        self._store = store

    def items(self, limit: int = 10) -> list[Path]:
        seen: set[Path] = set()
        result: list[Path] = []
        for entry in self._store.top(limit):
            if entry.path not in seen:
                seen.add(entry.path)
                result.append(entry.path)
        return result
