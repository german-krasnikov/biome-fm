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

    def register(self, entry: CommandEntry) -> None:
        self._entries.append(entry)

    def search(self, query: str) -> list[CommandEntry]:
        if not query:
            return list(self._entries)
        q = query.lower()
        return [e for e in self._entries if q in e.name.lower()]
