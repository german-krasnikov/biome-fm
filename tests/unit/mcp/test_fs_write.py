"""Unit tests for mcp/tools/fs_write.py — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.base import CommandHistory
from biome_fm.mcp.tools import _validate_path
from biome_fm.mcp.tools.fs_write import (
    _copy_files,
    _delete_files,
    _mkdir,
    _move_files,
    _rename_file,
    _undo_last,
)
from biome_fm.models.vfs_router import VFSRouter


@pytest.fixture
def vfs() -> VFSRouter:
    return VFSRouter()


@pytest.fixture
def history() -> CommandHistory:
    return CommandHistory()


# --- copy ---

def test_copy_creates_file(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    src = tmp_path / "a.txt"
    src.write_text("hi")
    dst_dir = tmp_path / "dest"
    dst_dir.mkdir()
    result = _copy_files([str(src)], str(dst_dir), vfs, history)
    assert result["copied"] == 1
    assert (dst_dir / "a.txt").exists()


def test_copy_records_history(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    src = tmp_path / "a.txt"
    src.write_text("hi")
    dst_dir = tmp_path / "dest"
    dst_dir.mkdir()
    _copy_files([str(src)], str(dst_dir), vfs, history)
    assert history.can_undo


# --- move ---

def test_move_file(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    src = tmp_path / "a.txt"
    src.write_text("hi")
    dst_dir = tmp_path / "dest"
    dst_dir.mkdir()
    result = _move_files([str(src)], str(dst_dir), vfs, history)
    assert result["moved"] == 1
    assert not src.exists()
    assert (dst_dir / "a.txt").exists()


# --- delete ---

def test_delete_file(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    f = tmp_path / "bye.txt"
    f.write_text("x")
    result = _delete_files([str(f)], vfs, history)
    assert result["deleted"] == 1
    assert not f.exists()


# --- mkdir ---

def test_mkdir_creates(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    new_dir = tmp_path / "newdir"
    result = _mkdir(str(new_dir), vfs, history)
    assert new_dir.is_dir()
    assert result["created"] == str(new_dir)


# --- rename ---

def test_rename_file(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    f = tmp_path / "old.txt"
    f.write_text("x")
    result = _rename_file(str(f), "new.txt", vfs, history)
    assert not f.exists()
    assert (tmp_path / "new.txt").exists()
    assert "old" in result["old"]
    assert "new" in result["new"]


# --- undo ---

def test_undo_last_undoes_copy(tmp_path: Path, vfs: VFSRouter, history: CommandHistory) -> None:
    src = tmp_path / "a.txt"
    src.write_text("hi")
    dst_dir = tmp_path / "dest"
    dst_dir.mkdir()
    _copy_files([str(src)], str(dst_dir), vfs, history)
    assert (dst_dir / "a.txt").exists()
    result = _undo_last(history)
    assert result["undone"] is True
    assert not (dst_dir / "a.txt").exists()


def test_undo_last_nothing_to_undo(history: CommandHistory) -> None:
    result = _undo_last(history)
    assert result["undone"] is False
    assert "reason" in result


# --- path traversal ---

def test_validate_path_allows_within_root(tmp_path: Path) -> None:
    child = tmp_path / "sub" / "file.txt"
    resolved = _validate_path(str(child), allowed_roots=[tmp_path])
    assert resolved == child.resolve()


def test_validate_path_rejects_escape(tmp_path: Path) -> None:
    other = Path("/tmp")
    with pytest.raises(PermissionError):
        _validate_path(str(other), allowed_roots=[tmp_path])
