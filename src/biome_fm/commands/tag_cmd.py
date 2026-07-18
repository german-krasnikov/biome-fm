"""Batch tag assign/remove command with undo. F283."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.base import Command
from biome_fm.models.tag_store import TagStore


class TagCmd(Command):
    description = "Batch tag"

    def __init__(
        self,
        paths: list[Path],
        add_tags: list[str],
        remove_tags: list[str],
        store: TagStore,
    ) -> None:
        self._paths = paths
        self._add = add_tags
        self._remove = set(remove_tags)
        self._store = store
        self._prev: dict[Path, list[str]] = {}

    def execute(self) -> None:
        self._prev = {p: self._store.get_tags(p) for p in self._paths}
        for p in self._paths:
            merged = list(dict.fromkeys(self._prev[p] + self._add))
            merged = [t for t in merged if t not in self._remove]
            self._store.set_tags(p, merged)
        self._store.save()

    def undo(self) -> None:
        for p, tags in self._prev.items():
            self._store.set_tags(p, tags)
        self._store.save()
