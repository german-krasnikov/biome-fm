"""TDD: Keyboard Macro Recorder — F457."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.presenters.macro_recorder import MacroPlayer, MacroRecorder


# ---------------------------------------------------------------------------
# MacroRecorder
# ---------------------------------------------------------------------------

def test_recorder_start_record_stop():
    r = MacroRecorder()
    r.start()
    r.record("copy")
    r.record("paste")
    assert r.stop() == ["copy", "paste"]


def test_recorder_record_before_start():
    r = MacroRecorder()
    r.record("x")
    assert r.stop() == []


def test_recorder_is_recording():
    r = MacroRecorder()
    assert not r.is_recording
    r.start()
    assert r.is_recording
    r.stop()
    assert not r.is_recording


# ---------------------------------------------------------------------------
# MacroStore
# ---------------------------------------------------------------------------

def test_macro_store_roundtrip(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("test", ["a", "b"])
    assert store.load_macro("test") == ["a", "b"]


def test_macro_store_delete(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("test", ["a"])
    store.delete("test")
    assert store.load_macro("test") is None


def test_macro_store_list(tmp_path):
    from biome_fm.models.macro_store import MacroStore

    store = MacroStore(tmp_path / "macros.json")
    store.save("alpha", ["x"])
    store.save("beta", ["y"])
    names = store.list_macros()
    assert set(names) == {"alpha", "beta"}


# ---------------------------------------------------------------------------
# MacroPlayer
# ---------------------------------------------------------------------------

def test_player_plays_commands():
    called = []

    class _FakeEntry:
        def __init__(self, name: str):
            self.name = name
            self.callback = lambda: called.append(name)

    class _FakeRegistry:
        _entries = [_FakeEntry("copy"), _FakeEntry("paste")]

    player = MacroPlayer(_FakeRegistry())
    player.play(["copy"])
    assert called == ["copy"]
