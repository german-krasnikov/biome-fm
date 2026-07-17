"""Tests for CommandStore — TDD Red phase."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.command_store import CommandStore, UserCommand


def _store(tmp_path: Path) -> CommandStore:
    return CommandStore(tmp_path / "commands.toml")


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    assert _store(tmp_path).commands == []


def test_roundtrip_single_command(tmp_path: Path) -> None:
    p = tmp_path / "commands.toml"
    s = CommandStore(p)
    s.add(UserCommand(id="t1", label="Test", command="echo $d", shortcut="Ctrl+T"))
    s.save()
    s2 = CommandStore(p)
    assert len(s2.commands) == 1
    c = s2.commands[0]
    assert c.id == "t1"
    assert c.label == "Test"
    assert c.command == "echo $d"
    assert c.shortcut == "Ctrl+T"


def test_roundtrip_multiple_commands(tmp_path: Path) -> None:
    p = tmp_path / "commands.toml"
    s = CommandStore(p)
    for i in range(3):
        s.add(UserCommand(id=f"c{i}", label=f"Cmd{i}", command=f"run{i}"))
    s.save()
    s2 = CommandStore(p)
    assert [c.id for c in s2.commands] == ["c0", "c1", "c2"]


def test_add_replaces_existing_by_id(tmp_path: Path) -> None:
    s = _store(tmp_path)
    s.add(UserCommand(id="x", label="Old", command="old"))
    s.add(UserCommand(id="x", label="New", command="new"))
    assert len(s.commands) == 1
    assert s.commands[0].label == "New"


def test_remove_deletes_command(tmp_path: Path) -> None:
    s = _store(tmp_path)
    s.add(UserCommand(id="rm", label="Gone", command="bye"))
    s.remove("rm")
    assert s.commands == []


def test_load_ignores_unknown_keys(tmp_path: Path) -> None:
    p = tmp_path / "commands.toml"
    p.write_text(
        '[[commands]]\nid = "ok"\nlabel = "OK"\ncommand = "ls"\nextra_key = "ignored"\n'
    )
    s = CommandStore(p)
    assert len(s.commands) == 1
    assert s.commands[0].id == "ok"
