"""Fuzzy file finder presenter — no Qt."""
from __future__ import annotations

import difflib
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True, slots=True)
class FuzzyMatch:
    score: float
    path: Path
    label: str  # relative path from root for display


class FuzzyPresenter:
    MAX_DEPTH = 5
    MAX_FILES = 10_000
    TOP_N = 100

    def scan(self, root: Path, cancel: threading.Event,
             on_done: Callable[[list[Path]], None]) -> None:
        """Walk root up to MAX_DEPTH in a daemon thread. Calls on_done(paths) when finished."""
        def _worker() -> None:
            paths: list[Path] = []
            try:
                for p in self._walk(root, cancel, depth=0):
                    paths.append(p)
                    if len(paths) >= self.MAX_FILES:
                        break
            except Exception:
                pass
            on_done(paths)

        threading.Thread(target=_worker, daemon=True).start()

    def _walk(self, root: Path, cancel: threading.Event, depth: int):
        if depth >= self.MAX_DEPTH or cancel.is_set():
            return
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return
        for entry in entries:
            if cancel.is_set():
                return
            if entry.name.startswith("."):
                continue
            if entry.is_file():
                yield entry
            elif entry.is_dir():
                yield from self._walk(entry, cancel, depth + 1)

    def score(self, query: str, paths: list[Path], root: Path) -> list[FuzzyMatch]:
        """Score paths against query. Returns top TOP_N sorted desc by score."""
        if not query:
            return [FuzzyMatch(1.0, p, self._label(p, root)) for p in paths[:self.TOP_N]]
        q = query.lower()
        scored: list[FuzzyMatch] = []
        for p in paths:
            ratio = difflib.SequenceMatcher(None, q, p.name.lower()).ratio()
            if ratio > 0.3:
                scored.append(FuzzyMatch(ratio, p, self._label(p, root)))
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:self.TOP_N]

    @staticmethod
    def _label(p: Path, root: Path) -> str:
        try:
            return str(p.relative_to(root))
        except ValueError:
            return p.name
