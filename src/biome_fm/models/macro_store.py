"""JSON-backed macro storage."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models._store_base import atomic_write_json, read_json


class MacroStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._macros: dict[str, list[str]] = {}

    def load(self) -> None:
        self._macros = read_json(self._path)

    def _persist(self) -> None:
        atomic_write_json(self._path, self._macros)

    def save(self, name: str, command_ids: list[str]) -> None:
        self._macros[name] = command_ids
        self._persist()

    def load_macro(self, name: str) -> list[str] | None:
        return self._macros.get(name)

    def list_macros(self) -> list[str]:
        return list(self._macros.keys())

    def delete(self, name: str) -> None:
        self._macros.pop(name, None)
        self._persist()
