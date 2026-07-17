"""Tests for ConflictResolver and auto_rename — pure Python, no Qt."""
import threading
from pathlib import Path

import pytest

from biome_fm.models.conflict_resolver import ConflictAction, ConflictResolver, auto_rename


# ── auto_rename ───────────────────────────────────────────────────────────────

def test_auto_rename_existing_file(tmp_path):
    dst = tmp_path / "foo.txt"
    dst.write_text("existing")
    result = auto_rename(dst)
    assert result == tmp_path / "foo_1.txt"


def test_auto_rename_multiple_conflicts(tmp_path):
    dst = tmp_path / "foo.txt"
    dst.write_text("x")
    (tmp_path / "foo_1.txt").write_text("x")
    result = auto_rename(dst)
    assert result == tmp_path / "foo_2.txt"


def test_auto_rename_no_conflict(tmp_path):
    dst = tmp_path / "ghost.txt"
    # dst doesn't exist — should return unchanged
    assert auto_rename(dst) == dst


def test_auto_rename_no_extension(tmp_path):
    dst = tmp_path / "readme"
    dst.write_text("x")
    result = auto_rename(dst)
    assert result == tmp_path / "readme_1"


# ── ConflictResolver ──────────────────────────────────────────────────────────

def test_ask_overwrite_reply(tmp_path):
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(ConflictAction.OVERWRITE)
    assert r.ask(tmp_path / "a", tmp_path / "b") == ConflictAction.OVERWRITE


def test_ask_skip_all_subsequent_skips(tmp_path):
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(ConflictAction.SKIP_ALL)
    r.ask(tmp_path / "a", tmp_path / "b")  # sets apply_all
    called = []
    r.on_conflict = lambda *_: called.append(1)  # must NOT be called again
    assert r.ask(tmp_path / "c", tmp_path / "d") == ConflictAction.SKIP_ALL
    assert not called


def test_ask_overwrite_all_subsequent(tmp_path):
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(ConflictAction.OVERWRITE_ALL)
    r.ask(tmp_path / "a", tmp_path / "b")
    assert r.ask(tmp_path / "c", tmp_path / "d") == ConflictAction.OVERWRITE_ALL


def test_ask_cancel_reply(tmp_path):
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(ConflictAction.CANCEL)
    assert r.ask(tmp_path / "a", tmp_path / "b") == ConflictAction.CANCEL


def test_on_conflict_callback_receives_src_dst(tmp_path):
    src, dst = tmp_path / "a.txt", tmp_path / "b.txt"
    r = ConflictResolver()
    calls: list = []

    def cb(s, d, res):
        calls.append((s, d))
        res.reply(ConflictAction.SKIP)

    r.on_conflict = cb
    r.ask(src, dst)
    assert calls == [(src, dst)]


def test_ask_timeout_returns_cancel():
    r = ConflictResolver(timeout=0.05)
    r.on_conflict = lambda *_: None  # never replies
    result = r.ask(Path("/a"), Path("/b"))
    assert result == ConflictAction.CANCEL


def test_reset_clears_apply_all(tmp_path):
    r = ConflictResolver()
    r.on_conflict = lambda s, d, res: res.reply(ConflictAction.SKIP_ALL)
    r.ask(tmp_path / "a", tmp_path / "b")
    r.reset()
    called = []
    r.on_conflict = lambda s, d, res: (called.append(1), res.reply(ConflictAction.OVERWRITE))
    r.ask(tmp_path / "c", tmp_path / "d")
    assert called  # on_conflict was called again after reset
