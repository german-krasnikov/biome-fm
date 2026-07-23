"""ShortcutStore — JSON-backed {action: key_sequence} map."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models._store_base import atomic_write_json, read_json


class ShortcutStore:
    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        self._data: dict[str, str] = {}

    def get(self, action: str, default: str = "") -> str:
        return self._data.get(action, default)

    def set(self, action: str, keyseq: str) -> None:
        self._data[action] = keyseq

    def all(self) -> dict[str, str]:
        return dict(self._data)

    def save(self) -> None:
        atomic_write_json(self._path, self._data)

    def load(self) -> None:
        self._data = read_json(self._path)
