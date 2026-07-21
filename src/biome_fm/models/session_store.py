"""SessionStore — JSON-backed named sessions (F267)."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from biome_fm.session import PanelSession, PaneSideState, SessionState, TabState


def _decode(data: dict) -> SessionState | None:
    try:
        left = PaneSideState(
            tabs=[TabState(**t) for t in data["left"]["tabs"]],
            active_idx=data["left"].get("active_idx", 0),
            view_mode=data["left"].get("view_mode", "detail"),
        )
        right = PaneSideState(
            tabs=[TabState(**t) for t in data["right"]["tabs"]],
            active_idx=data["right"].get("active_idx", 0),
            view_mode=data["right"].get("view_mode", "detail"),
        )
        if not left.tabs or not right.tabs:
            return None
        preview = PanelSession(**data["preview"]) if "preview" in data else PanelSession()
        ai = PanelSession(**data["ai"]) if "ai" in data else PanelSession()
        return SessionState(left=left, right=right, preview=preview, ai=ai)
    except (KeyError, TypeError):
        return None


class SessionStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> dict[str, dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def save_named_session(self, name: str, state: SessionState) -> None:
        data = self._load()
        data[name] = asdict(state)
        self._save(data)

    def load_named_session(self, name: str) -> SessionState | None:
        raw = self._load().get(name)
        return _decode(raw) if raw is not None else None

    def list_sessions(self) -> list[str]:
        return list(self._load().keys())

    def delete_session(self, name: str) -> None:
        data = self._load()
        data.pop(name, None)
        self._save(data)
