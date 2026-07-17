"""ShortcutStore — JSON-backed {action: key_sequence} map."""
from __future__ import annotations

import json
from pathlib import Path


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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def load(self) -> None:
        if not self._path.exists():
            return
        self._data = json.loads(self._path.read_text(encoding="utf-8"))
