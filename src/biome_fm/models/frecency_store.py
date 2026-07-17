"""Frecency-based directory visit tracker. score = visits / (age_secs + 3600)."""
from __future__ import annotations

import atexit
import json
import time
from dataclasses import dataclass
from pathlib import Path

_MAX = 200


@dataclass
class FrecencyEntry:
    path: Path
    visits: int
    last_visit: float


class FrecencyStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, dict] = {}
        self._load_from_disk()
        atexit.register(self._flush)

    def score(self, entry: FrecencyEntry) -> float:
        age = time.time() - entry.last_visit + 3600
        return entry.visits / age

    def record(self, path: Path) -> None:
        key = str(path)
        if key in self._data:
            self._data[key]["visits"] += 1
            self._data[key]["last_visit"] = time.time()
        else:
            self._data[key] = {"visits": 1, "last_visit": time.time()}
            if len(self._data) > _MAX:
                # evict lowest-scored entry
                worst = min(self._data, key=lambda k: self._entry_score(k))
                del self._data[worst]

    def top(self, n: int = 20) -> list[FrecencyEntry]:
        entries = [self._to_entry(k, v) for k, v in self._data.items()]
        entries.sort(key=self.score, reverse=True)
        return entries[:n]

    def _entry_score(self, key: str) -> float:
        return self.score(self._to_entry(key, self._data[key]))

    @staticmethod
    def _to_entry(key: str, raw: dict) -> FrecencyEntry:
        return FrecencyEntry(path=Path(key), visits=raw["visits"], last_visit=raw["last_visit"])

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data))
        tmp.replace(self._path)

    def _load_from_disk(self) -> None:
        if not self._path.exists():
            return
        try:
            self._data = json.loads(self._path.read_text())
        except Exception:
            pass
