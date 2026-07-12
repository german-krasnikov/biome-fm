"""TOML-backed bookmark list."""
from __future__ import annotations

import tomllib
from pathlib import Path


class BookmarkStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._items: list[Path] = []
        self._load()

    def add(self, path: Path) -> None:
        if path not in self._items:
            self._items.append(path)
            self._save()

    def remove(self, path: Path) -> None:
        if path in self._items:
            self._items.remove(path)
            self._save()

    def move_up(self, path: Path) -> None:
        if path not in self._items:
            return
        i = self._items.index(path)
        if i > 0:
            self._items[i - 1], self._items[i] = self._items[i], self._items[i - 1]
            self._save()

    def move_down(self, path: Path) -> None:
        if path not in self._items:
            return
        i = self._items.index(path)
        if i < len(self._items) - 1:
            self._items[i], self._items[i + 1] = self._items[i + 1], self._items[i]
            self._save()

    def replace(self, old: Path, new: Path) -> None:
        if old in self._items:
            self._items[self._items.index(old)] = new
            self._save()

    def all(self) -> list[Path]:
        return list(self._items)

    def __contains__(self, path: Path) -> bool:
        return path in self._items

    def _save(self) -> None:
        items = ", ".join(f'"{p}"' for p in self._items)
        lines = ["[bookmarks]\n", f"paths = [{items}]\n"]
        self._path.write_text("".join(lines))

    def _load(self) -> None:
        if not self._path.exists():
            return
        data = tomllib.loads(self._path.read_text())
        self._items = [Path(s) for s in data.get("bookmarks", {}).get("paths", [])]
