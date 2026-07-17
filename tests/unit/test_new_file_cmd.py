"""Tests for NewFileCmd."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.new_file_cmd import NewFileCmd


def test_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "hello.txt"
    NewFileCmd(p).execute()
    assert p.exists()


def test_writes_content(tmp_path: Path) -> None:
    p = tmp_path / "script.py"
    NewFileCmd(p, b"# hello\n").execute()
    assert p.read_bytes() == b"# hello\n"


def test_undo_deletes(tmp_path: Path) -> None:
    p = tmp_path / "bye.txt"
    cmd = NewFileCmd(p)
    cmd.execute()
    assert p.exists()
    cmd.undo()
    assert not p.exists()


def test_undo_missing_ok(tmp_path: Path) -> None:
    p = tmp_path / "ghost.txt"
    NewFileCmd(p).undo()  # never executed — must not raise
