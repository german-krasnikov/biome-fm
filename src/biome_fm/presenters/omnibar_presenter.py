"""Qt-free omnibar presenter — prefix dispatch."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from biome_fm.utils.path_completion import path_completions


class OmniMode(Enum):
    NAVIGATE = auto()
    COMMAND = auto()
    SEARCH = auto()


@dataclass(frozen=True)
class OmniItem:
    label: str
    subtitle: str = ""
    data: object = None


class OmnibarPresenter:
    def __init__(self, registry, root: Path = Path.home()) -> None:
        self._registry = registry
        self._root = root

    def set_root(self, root: Path) -> None:
        self._root = root

    def mode_for(self, text: str) -> OmniMode:
        if text.startswith(">"):
            return OmniMode.COMMAND
        if text.startswith(("/", "~", ".")):
            return OmniMode.NAVIGATE
        return OmniMode.SEARCH

    def query_changed(self, text: str) -> list[OmniItem]:
        mode = self.mode_for(text)
        if mode == OmniMode.COMMAND:
            return self._cmd_items(text[1:])
        if mode == OmniMode.NAVIGATE:
            return self._nav_items(text)
        return self._search_items(text)

    def _nav_items(self, text: str) -> list[OmniItem]:
        return [OmniItem(label=p, data=Path(p)) for p in path_completions(text)[:20]]

    def _cmd_items(self, query: str) -> list[OmniItem]:
        return [
            OmniItem(label=e.name, subtitle=e.shortcut, data=e.name)
            for e in self._registry.search(query)[:20]
        ]

    def _search_items(self, text: str) -> list[OmniItem]:
        if not text:
            return []
        try:
            return [
                OmniItem(label=p.name, subtitle=str(p.parent), data=p)
                for p in self._root.iterdir()
                if text.lower() in p.name.lower()
            ][:20]
        except OSError:
            return []
