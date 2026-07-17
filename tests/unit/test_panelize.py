"""Tests for panelize utility."""
from __future__ import annotations

from pathlib import Path

from biome_fm.utils.panelize import parse_shell_output


def test_absolute_paths_parsed(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("x")
    items = parse_shell_output(str(f) + "\n", cwd=tmp_path)
    assert len(items) == 1
    assert items[0].name == "a.txt"


def test_relative_paths_resolved(tmp_path: Path) -> None:
    f = tmp_path / "b.txt"
    f.write_text("x")
    items = parse_shell_output("b.txt\n", cwd=tmp_path)
    assert len(items) == 1
    assert items[0].path == f


def test_nonexistent_skipped(tmp_path: Path) -> None:
    items = parse_shell_output("/no/such/file.txt\n", cwd=tmp_path)
    assert items == []


def test_empty_output(tmp_path: Path) -> None:
    assert parse_shell_output("", cwd=tmp_path) == []
