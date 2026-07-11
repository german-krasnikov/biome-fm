"""Tests for session.py — JSON persistence."""
from __future__ import annotations

from pathlib import Path

from biome_fm.session import (
    PaneSideState,
    SessionState,
    TabState,
    load_session,
    save_session,
)


def test_load_missing_returns_none(tmp_path: Path) -> None:
    assert load_session(tmp_path / "no.json") is None


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    state = SessionState(
        left=PaneSideState(tabs=[TabState("/home/user")], active_idx=0),
        right=PaneSideState(tabs=[TabState("/tmp")], active_idx=0),
    )
    save_session(state, p)
    loaded = load_session(p)
    assert loaded is not None
    assert loaded.left.tabs[0].path == "/home/user"
    assert loaded.right.tabs[0].path == "/tmp"


def test_corrupted_json_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    p.write_text("{broken json", encoding="utf-8")
    assert load_session(p) is None


def test_default_session_state_has_home(tmp_path: Path) -> None:
    state = SessionState()
    assert state.left.tabs[0].path == str(Path.home())
    assert state.right.tabs[0].path == str(Path.home())


def test_multiple_tabs_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    state = SessionState(
        left=PaneSideState(
            tabs=[TabState("/a"), TabState("/b"), TabState("/c")],
            active_idx=2,
        ),
        right=PaneSideState(tabs=[TabState("/d")], active_idx=0),
    )
    save_session(state, p)
    loaded = load_session(p)
    assert loaded is not None
    assert len(loaded.left.tabs) == 3
    assert loaded.left.tabs[2].path == "/c"


def test_active_idx_preserved(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    state = SessionState(
        left=PaneSideState(tabs=[TabState("/a"), TabState("/b")], active_idx=1),
        right=PaneSideState(tabs=[TabState("/c")], active_idx=0),
    )
    save_session(state, p)
    loaded = load_session(p)
    assert loaded is not None
    assert loaded.left.active_idx == 1


def test_missing_key_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    p.write_text('{"left": {"tabs": []}}', encoding="utf-8")
    assert load_session(p) is None


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "session.json"
    save_session(SessionState(), p)
    assert p.exists()
