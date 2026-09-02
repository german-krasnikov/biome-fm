"""Tests for NewFileCmd."""
from __future__ import annotations

from pathlib import Path

from biome_fm.commands.new_file_cmd import NewFileCmd


def test_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "hello.txt"
    NewFileCmd(p).execute()
    assert p.exists()


def test_writes_content(tmp_path: Path) -> None:
    p = tmp_path / "script.py"
    NewFileCmd(p, b"# hello\n").execute()
    assert p.read_bytes() == b"# hello\n"


def test_execute_creates_file(tmp_path: Path) -> None:
    """Regression guard: execute() still creates the file after undo() removal."""
    p = tmp_path / "guard.txt"
    NewFileCmd(p, b"content").execute()
    assert p.exists()
    assert p.read_bytes() == b"content"
