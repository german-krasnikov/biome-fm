"""JSON-backed per-directory view state with LRU eviction (max 500 entries)."""
from __future__ import annotations

import atexit
import json
from collections import OrderedDict
from pathlib import Path

from biome_fm.models.view_state import ViewState

_MAX = 500


class DirStateStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: OrderedDict[str, dict] = OrderedDict()
        self._load_from_disk()
        atexit.register(self._flush)

    def save(self, dir_path: Path, state: ViewState) -> None:
        key = str(dir_path)
        self._data.pop(key, None)
        self._data[key] = {"sort_col": state.sort_col, "sort_asc": state.sort_asc, "filter": state.filter}
        if len(self._data) > _MAX:
            self._data.popitem(last=False)  # evict oldest

    def load(self, dir_path: Path) -> ViewState | None:
        raw = self._data.get(str(dir_path))
        if raw is None:
            return None
        return ViewState(sort_col=raw["sort_col"], sort_asc=raw["sort_asc"], filter=raw["filter"])

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(dict(self._data)))
        tmp.replace(self._path)

    def _load_from_disk(self) -> None:
        if not self._path.exists():
            return
        try:
            raw: dict = json.loads(self._path.read_text())
            for k, v in raw.items():
                self._data[k] = v
        except Exception:
            pass
