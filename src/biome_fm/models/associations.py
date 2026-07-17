"""FileAssociations — maps file suffixes to apps (Feature #21)."""
from __future__ import annotations

import json
from pathlib import Path


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
        self._path.write_text(json.dumps(self._data, indent=2))
