"""TOML-backed bookmark list."""
from __future__ import annotations

import tomllib
from pathlib import Path


class BookmarkStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._items: list[Path] = []
        self._names: dict[str, str] = {}
        self._load()

    def add(self, path: Path, name: str = "") -> None:
        if path not in self._items:
            self._items.append(path)
            if name:
                self._names[str(path)] = name
            self._save()

    def remove(self, path: Path) -> None:
        if path in self._items:
            self._items.remove(path)
            self._names.pop(str(path), None)
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
            old_name = self._names.pop(str(old), "")
            self._items[self._items.index(old)] = new
            if old_name:
                self._names[str(new)] = old_name
            self._save()

    def all(self) -> list[Path]:
        return list(self._items)

    def get_name(self, path: Path) -> str:
        return self._names.get(str(path), "")

    def set_name(self, path: Path, name: str) -> None:
        if path not in self._items:
            return
        if name:
            self._names[str(path)] = name
        else:
            self._names.pop(str(path), None)
        self._save()

    def display_label(self, path: Path) -> str:
        name = self.get_name(path)
        return name if name else (path.name or str(path))

    def __contains__(self, path: Path) -> bool:
        return path in self._items

    @staticmethod
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def _save(self) -> None:
        items = ", ".join(f'"{self._esc(str(p))}"' for p in self._items)
        names = [self._names.get(str(p), "") for p in self._items]
        names_str = ", ".join(f'"{self._esc(n)}"' for n in names)
        lines = ["[bookmarks]\n", f"paths = [{items}]\n", f"names = [{names_str}]\n"]
        self._path.write_text("".join(lines), encoding="utf-8")

    def _load(self) -> None:
        if not self._path.exists():
            self._items = [p for p in self._default_paths() if p.is_dir()]
            self._names = {}
            if self._items:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._save()
            return
        try:
            data = tomllib.loads(self._path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            return
        bm = data.get("bookmarks", {})
        paths_raw = bm.get("paths", [])
        names_raw = bm.get("names", [])
        self._items = [Path(s) for s in paths_raw]
        self._names = {}
        for i, p in enumerate(self._items):
            if i < len(names_raw) and names_raw[i]:
                self._names[str(p)] = names_raw[i]

    @staticmethod
    def _default_paths() -> list[Path]:
        home = Path.home()
        return [home, home / "Desktop", home / "Documents", home / "Downloads"]
