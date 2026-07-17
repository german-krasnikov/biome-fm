"""WorkspaceStore — save/load/delete named workspace presets in JSON."""
from __future__ import annotations

import json
from pathlib import Path


class WorkspaceStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _data(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def list_names(self) -> list[str]:
        return sorted(self._data().keys())

    def save(self, name: str, left_paths: list[str], right_paths: list[str]) -> None:
        d = self._data()
        d[name] = {"left": left_paths, "right": right_paths}
        self._path.write_text(json.dumps(d, indent=2), encoding="utf-8")

    def load(self, name: str) -> dict | None:
        """Returns {"left": [...], "right": [...]} or None."""
        return self._data().get(name)

    def delete(self, name: str) -> None:
        d = self._data()
        d.pop(name, None)
        self._path.write_text(json.dumps(d, indent=2), encoding="utf-8")
