"""Tests for ReplaceCmd and search_replace — F023 multi-file find & replace."""
from __future__ import annotations

import pytest
from pathlib import Path

from biome_fm.commands.replace_cmd import ReplaceCmd, ReplaceResult, search_replace


def test_replace_in_file(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("foo bar foo")
    result = ReplaceCmd(f, "foo", "baz").execute()
    assert f.read_text() == "baz bar baz"
    assert result.count == 2


def test_dry_run_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("foo bar")
    results = search_replace([f], "foo", "baz", dry_run=True)
    assert results[0].count == 1
    assert f.read_text() == "foo bar"  # file untouched


def test_replace_count(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("x x x")
    results = search_replace([f], "x", "y")
    assert results[0].count == 3


def test_backup_created(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("foo")
    ReplaceCmd(f, "foo", "bar").execute()
    assert (tmp_path / "a.txt.bak").exists()


def test_undo_restores_backup(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("foo")
    cmd = ReplaceCmd(f, "foo", "bar")
    cmd.execute()
    assert f.read_text() == "bar"
    cmd.undo()
    assert f.read_text() == "foo"
    assert not (tmp_path / "a.txt.bak").exists()


def test_regex_replace(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("hello 123 world 456")
    results = search_replace([f], r"\d+", "NUM", regex=True)
    assert f.read_text() == "hello NUM world NUM"
    assert results[0].count == 2


def test_binary_file_skipped(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(bytes(range(256)))  # >30% non-printable → binary
    results = search_replace([f], "foo", "bar")
    assert results == []
