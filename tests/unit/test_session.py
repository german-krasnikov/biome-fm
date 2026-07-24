"""Tests for session.py — JSON persistence."""
from __future__ import annotations

from pathlib import Path

from biome_fm.session import (
    PanelSession,
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


def test_panel_session_defaults() -> None:
    ps = PanelSession()
    assert ps.state == "hidden"
    assert ps.float_geometry == ""


def test_panel_session_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    state = SessionState(
        left=PaneSideState(tabs=[TabState("/a")], active_idx=0),
        right=PaneSideState(tabs=[TabState("/b")], active_idx=0),
        preview=PanelSession(state="overlay", float_geometry=""),
        ai=PanelSession(state="floating", float_geometry="10,20,600,800"),
    )
    save_session(state, p)
    loaded = load_session(p)
    assert loaded is not None
    assert loaded.preview.state == "overlay"
    assert loaded.ai.state == "floating"
    assert loaded.ai.float_geometry == "10,20,600,800"


def test_old_session_without_panels_loads_with_defaults(tmp_path: Path) -> None:
    """Backward compat: old JSON without preview/ai fields."""
    p = tmp_path / "session.json"
    p.write_text(
        '{"left": {"tabs": [{"path": "/a"}], "active_idx": 0},'
        ' "right": {"tabs": [{"path": "/b"}], "active_idx": 0}}',
        encoding="utf-8",
    )
    loaded = load_session(p)
    assert loaded is not None
    assert loaded.preview.state == "hidden"
    assert loaded.ai.state == "hidden"


def test_save_session_no_tmp_file_left(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    save_session(SessionState(), p)
    assert not p.with_suffix(".json.tmp").exists()


def test_save_session_overwrites_stale_tmp(tmp_path: Path) -> None:
    p = tmp_path / "session.json"
    p.with_suffix(".json.tmp").write_text("stale junk", encoding="utf-8")
    save_session(SessionState(), p)
    assert load_session(p) is not None


def test_save_session_target_untouched_on_failure(tmp_path: Path, monkeypatch) -> None:
    import pytest
    p = tmp_path / "session.json"
    save_session(SessionState(), p)

    def boom(path, content, encoding="utf-8"):
        raise OSError("simulated crash")

    monkeypatch.setattr("biome_fm.session.atomic_write", boom)
    with pytest.raises(OSError):
        save_session(SessionState(), p)

    assert load_session(p) is not None
