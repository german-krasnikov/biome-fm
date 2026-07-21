"""JSON-backed macro storage."""
from __future__ import annotations

import json
from pathlib import Path


class MacroStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._macros: dict[str, list[str]] = {}

    def load(self) -> None:
        if self._path.exists():
            self._macros = json.loads(self._path.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._macros, indent=2), encoding="utf-8")

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
