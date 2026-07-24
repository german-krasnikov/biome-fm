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
    FRECENCY = auto()
    PROJECT = auto()


@dataclass(frozen=True)
class OmniItem:
    label: str
    subtitle: str = ""
    data: object = None


class OmnibarPresenter:
    def __init__(self, registry, root: Path = Path.home(), frecency=None) -> None:
        self._registry = registry
        self._root = root
        self._frecency = frecency

    def set_root(self, root: Path) -> None:
        self._root = root

    def mode_for(self, text: str) -> OmniMode:
        if text.startswith("@"):
            return OmniMode.PROJECT
        if text.startswith(">"):
            return OmniMode.COMMAND
        if text.startswith(":"):
            return OmniMode.FRECENCY
        if text.startswith(("/", "~", ".")):
            return OmniMode.NAVIGATE
        return OmniMode.SEARCH

    def query_changed(self, text: str) -> list[OmniItem]:
        mode = self.mode_for(text)
        if mode == OmniMode.PROJECT:
            return self._project_items(text[1:])
        if mode == OmniMode.COMMAND:
            return self._cmd_items(text[1:])
        if mode == OmniMode.FRECENCY:
            return self._frecency_items(text[1:])
        if mode == OmniMode.NAVIGATE:
            return self._nav_items(text)
        return self._search_items(text)

    def _project_items(self, query: str) -> list[OmniItem]:
        # ponytail: synchronous detect_project() for 50 paths; move to ThreadPoolExecutor if startup feels slow
        if self._frecency is None:
            return []
        from biome_fm.models.project_detector import detect_project  # local import avoids cycle
        q = query.lower()
        results: list[OmniItem] = []
        seen: set[Path] = set()
        for e in self._frecency.top(50):
            info = detect_project(e.path)
            if info is None or info.root in seen:
                continue
            if q and q not in str(info.root).lower() and q not in info.name.lower():
                continue
            seen.add(info.root)
            results.append(OmniItem(label=info.name, subtitle=f"{info.type} · {info.root}", data=info.root))
            if len(results) >= 20:
                break
        return results

    def _frecency_items(self, query: str) -> list[OmniItem]:
        if self._frecency is None:
            return []
        q = query.lower()
        entries = self._frecency.top(20)
        if q:
            entries = [e for e in entries if q in str(e.path).lower()]
        return [OmniItem(label=str(e.path), data=e.path) for e in entries]

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
