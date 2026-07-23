"""WorkspaceStore — save/load/delete named workspace presets in JSON."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models._store_base import atomic_write_json, read_json


class WorkspaceStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _data(self) -> dict:
        return read_json(self._path)  # type: ignore[return-value]

    def list_names(self) -> list[str]:
        return sorted(self._data().keys())

    def save(self, name: str, left_paths: list[str], right_paths: list[str]) -> None:
        d = self._data()
        d[name] = {"left": left_paths, "right": right_paths}
        atomic_write_json(self._path, d)

    def load(self, name: str) -> dict | None:
        """Returns {"left": [...], "right": [...]} or None."""
        return self._data().get(name)

    def delete(self, name: str) -> None:
        d = self._data()
        d.pop(name, None)
        atomic_write_json(self._path, d)
