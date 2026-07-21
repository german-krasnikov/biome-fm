"""TDD: F456 — view_mode field on PaneSideState."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.session import PaneSideState, SessionState, TabState, load_session, save_session
from biome_fm.models.session_store import SessionStore


def _minimal_json(left_vm: str | None = None, right_vm: str | None = None) -> dict:
    left: dict = {"tabs": [{"path": str(Path.home())}], "active_idx": 0}
    right: dict = {"tabs": [{"path": str(Path.home())}], "active_idx": 0}
    if left_vm is not None:
        left["view_mode"] = left_vm
    if right_vm is not None:
        right["view_mode"] = right_vm
    return {"left": left, "right": right}


def test_pane_side_state_default_view_mode():
    assert PaneSideState().view_mode == "detail"


def test_load_session_with_view_mode(tmp_path: Path):
    p = tmp_path / "session.json"
    p.write_text(json.dumps(_minimal_json("icon", "icon")), encoding="utf-8")
    state = load_session(p)
    assert state is not None
    assert state.left.view_mode == "icon"
    assert state.right.view_mode == "icon"


def test_load_session_without_view_mode(tmp_path: Path):
    p = tmp_path / "session.json"
    p.write_text(json.dumps(_minimal_json()), encoding="utf-8")
    state = load_session(p)
    assert state is not None
    assert state.left.view_mode == "detail"
    assert state.right.view_mode == "detail"


def test_save_load_roundtrip_view_mode(tmp_path: Path):
    p = tmp_path / "session.json"
    original = SessionState(
        left=PaneSideState(tabs=[TabState(str(Path.home()))], view_mode="gallery"),
        right=PaneSideState(tabs=[TabState(str(Path.home()))], view_mode="detail"),
    )
    save_session(original, p)
    restored = load_session(p)
    assert restored is not None
    assert restored.left.view_mode == "gallery"
    assert restored.right.view_mode == "detail"


def test_session_store_roundtrip_view_mode(tmp_path: Path):
    store = SessionStore(tmp_path / "named.json")
    state = SessionState(
        left=PaneSideState(tabs=[TabState(str(Path.home()))], view_mode="icon"),
        right=PaneSideState(tabs=[TabState(str(Path.home()))], view_mode="detail"),
    )
    store.save_named_session("work", state)
    restored = store.load_named_session("work")
    assert restored is not None
    assert restored.left.view_mode == "icon"
    assert restored.right.view_mode == "detail"
