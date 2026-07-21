"""Command palette registry — pure Python, no Qt dependency."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class CommandEntry:
    name: str
    shortcut: str
    callback: Callable[[], None]


class CommandRegistry:
    def __init__(self) -> None:
        self._entries: list[CommandEntry] = []
        self._hits: dict[str, int] = {}

    def register(self, entry: CommandEntry) -> None:
        self._entries.append(entry)

    def record_hit(self, name: str) -> None:
        self._hits[name] = self._hits.get(name, 0) + 1

    def get_entry(self, name: str) -> CommandEntry:
        for e in self._entries:
            if e.name == name:
                return e
        raise KeyError(name)

    def search(self, query: str) -> list[CommandEntry]:
        if not query:
            return sorted(self._entries, key=lambda e: self._hits.get(e.name, 0), reverse=True)
        q = query.lower()
        matches = [e for e in self._entries if q in e.name.lower()]
        return sorted(matches, key=lambda e: self._hits.get(e.name, 0), reverse=True)
