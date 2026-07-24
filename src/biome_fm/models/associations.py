"""FileAssociations — maps file suffixes to apps (Feature #21)."""
from __future__ import annotations

import json
from pathlib import Path

from biome_fm.models._store_base import atomic_write_json


class FileAssociations:
    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        try:
            self._data: dict[str, str] = json.loads(config_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def get(self, suffix: str) -> str | None:
        return self._data.get(suffix)

    def set(self, suffix: str, app: str) -> None:
        self._data[suffix] = app

    def save(self) -> None:
        atomic_write_json(self._path, self._data)
