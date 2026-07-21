"""Unit tests for F422 — Folder Watch Rules."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.watch_rules import WatchRule, WatchRuleEngine, WatchRuleStore


# ---------------------------------------------------------------------------
# WatchRuleStore
# ---------------------------------------------------------------------------

def test_store_load_empty(tmp_path: Path) -> None:
    store = WatchRuleStore(tmp_path / "nonexistent.toml")
    store.load()
    assert store.all() == []


def test_store_load_save_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    store = WatchRuleStore(path)
    store.add(WatchRule(watch_dir="/tmp/inbox", pattern="*.pdf", command="open {file}"))
    store.save()

    store2 = WatchRuleStore(path)
    store2.load()
    rules = store2.all()
    assert len(rules) == 1
    assert rules[0].watch_dir == "/tmp/inbox"
    assert rules[0].pattern == "*.pdf"
    assert rules[0].command == "open {file}"


def test_store_add_remove(tmp_path: Path) -> None:
    store = WatchRuleStore(tmp_path / "rules.toml")
    store.add(WatchRule("/a", "*.pdf", "cmd1"))
    store.add(WatchRule("/b", "*.txt", "cmd2"))
    store.remove(0)
    rules = store.all()
    assert len(rules) == 1
    assert rules[0].watch_dir == "/b"


def test_store_save_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "nested" / "rules.toml"
    store = WatchRuleStore(path)
    store.add(WatchRule("/x", "*.png", "echo {file}"))
    store.save()
    assert path.exists()


# ---------------------------------------------------------------------------
# WatchRuleEngine
# ---------------------------------------------------------------------------

def _make_store_with_rule(watch_dir: str, pattern: str = "*.pdf") -> WatchRuleStore:
    store = WatchRuleStore(Path("/dev/null"))  # won't be saved
    store.add(WatchRule(watch_dir=watch_dir, pattern=pattern, command="echo {file}"))
    return store


def test_engine_first_snapshot_no_fire(tmp_path: Path) -> None:
    (tmp_path / "existing.pdf").write_text("x")
    store = _make_store_with_rule(str(tmp_path))
    engine = WatchRuleEngine(store)
    result = engine.check_dir(str(tmp_path))
    assert result == []


def test_engine_detects_new_file(tmp_path: Path) -> None:
    (tmp_path / "existing.pdf").write_text("x")
    store = _make_store_with_rule(str(tmp_path))
    engine = WatchRuleEngine(store)
    engine.snapshot_dir(str(tmp_path))  # prime snapshot

    new_file = tmp_path / "new.pdf"
    new_file.write_text("y")

    with patch("biome_fm.models.watch_rules.subprocess.Popen") as mock_popen:
        result = engine.check_dir(str(tmp_path))

    assert len(result) == 1
    rule, path = result[0]
    assert path == new_file
    mock_popen.assert_called_once()


def test_engine_pattern_mismatch(tmp_path: Path) -> None:
    store = _make_store_with_rule(str(tmp_path), pattern="*.pdf")
    engine = WatchRuleEngine(store)
    engine.snapshot_dir(str(tmp_path))

    (tmp_path / "test.txt").write_text("z")

    with patch("biome_fm.models.watch_rules.subprocess.Popen") as mock_popen:
        result = engine.check_dir(str(tmp_path))

    assert result == []
    mock_popen.assert_not_called()


def test_engine_on_fired_callback(tmp_path: Path) -> None:
    store = _make_store_with_rule(str(tmp_path))
    fired_calls: list[tuple] = []
    engine = WatchRuleEngine(store, on_fired=lambda r, p: fired_calls.append((r, p)))
    engine.snapshot_dir(str(tmp_path))

    new_file = tmp_path / "report.pdf"
    new_file.write_text("data")

    with patch("biome_fm.models.watch_rules.subprocess.Popen"):
        engine.check_dir(str(tmp_path))

    assert len(fired_calls) == 1
    assert fired_calls[0][1] == new_file
