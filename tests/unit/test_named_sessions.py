"""F267 — Named Sessions: save/load/list/delete via SessionStore."""
from __future__ import annotations

import pytest
from pathlib import Path

from biome_fm.models.session_store import SessionStore
from biome_fm.session import PaneSideState, SessionState, TabState


def _state(left: str = "/home", right: str = "/tmp") -> SessionState:
    return SessionState(
        left=PaneSideState(tabs=[TabState(left)], active_idx=0),
        right=PaneSideState(tabs=[TabState(right)], active_idx=0),
    )


class TestNamedSessions:
    def test_save_and_load_session(self, tmp_path: Path) -> None:
        store = SessionStore(tmp_path / "sessions.json")
        state = _state("/home/user", "/tmp")
        store.save_named_session("work", state)
        loaded = store.load_named_session("work")
        assert loaded is not None
        assert loaded.left.tabs[0].path == "/home/user"
        assert loaded.right.tabs[0].path == "/tmp"

    def test_list_sessions(self, tmp_path: Path) -> None:
        store = SessionStore(tmp_path / "sessions.json")
        store.save_named_session("a", _state())
        store.save_named_session("b", _state())
        assert set(store.list_sessions()) == {"a", "b"}

    def test_delete_session(self, tmp_path: Path) -> None:
        store = SessionStore(tmp_path / "sessions.json")
        store.save_named_session("x", _state())
        store.delete_session("x")
        assert store.list_sessions() == []

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        store = SessionStore(tmp_path / "sessions.json")
        assert store.load_named_session("nope") is None
