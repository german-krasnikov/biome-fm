"""SessionStore — JSON-backed named sessions (F267)."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from biome_fm.models._store_base import atomic_write_json, read_json
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
        return read_json(self._path)  # type: ignore[return-value]

    def _save(self, data: dict[str, dict]) -> None:
        atomic_write_json(self._path, data)

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
