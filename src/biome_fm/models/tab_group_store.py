"""TabGroupStore — JSON-backed named tab groups."""
from __future__ import annotations

import json
from pathlib import Path


class TabGroupStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, list[str]]:
        try:
            return json.loads(self._path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict[str, list[str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data))

    def save_group(self, name: str, paths: list[Path]) -> None:
        data = self._load()
        data[name] = [str(p) for p in paths]
        self._save(data)

    def load_group(self, name: str) -> list[Path]:
        return [Path(p) for p in self._load().get(name, [])]

    def list_groups(self) -> list[str]:
        return list(self._load().keys())

    def delete_group(self, name: str) -> None:
        data = self._load()
        data.pop(name, None)
        self._save(data)
