"""Integration tests for file commands using real filesystem + LocalVFS."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.copy_cmd import CopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.commands.move_cmd import MoveCmd
from biome_fm.commands.rename_cmd import RenameCmd
from biome_fm.models.vfs import LocalVFS


@pytest.fixture()
def vfs() -> LocalVFS:
    return LocalVFS()


def test_copy_creates_file_and_undo_removes(tmp_path: Path, vfs: LocalVFS) -> None:
    src = tmp_path / "src"
    src.mkdir()
    f = src / "file.txt"
    f.write_text("hello")
    dst = tmp_path / "dst"
    dst.mkdir()

    cmd = CopyCmd([f], dst, vfs)
    cmd.execute()
    assert (dst / "file.txt").exists()

    cmd.undo()
    assert not (dst / "file.txt").exists()


def test_move_moves_file_and_undo_restores(tmp_path: Path, vfs: LocalVFS) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    f = src_dir / "file.txt"
    f.write_text("hello")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    cmd = MoveCmd([f], dst_dir, vfs)
    cmd.execute()
    assert (dst_dir / "file.txt").exists()
    assert not f.exists()

    cmd.undo()
    assert f.exists()
    assert not (dst_dir / "file.txt").exists()


def test_mkdir_creates_and_undo_removes(tmp_path: Path, vfs: LocalVFS) -> None:
    target = tmp_path / "newdir"
    cmd = MkdirCmd(target, vfs)
    cmd.execute()
    assert target.is_dir()

    cmd.undo()
    assert not target.exists()


def test_rename_changes_name_and_undo_restores(tmp_path: Path, vfs: LocalVFS) -> None:
    f = tmp_path / "old.txt"
    f.write_text("data")

    cmd = RenameCmd(f, "new.txt", vfs)
    cmd.execute()
    assert (tmp_path / "new.txt").exists()
    assert not f.exists()

    cmd.undo()
    assert f.exists()
    assert not (tmp_path / "new.txt").exists()


def test_delete_removes_file(tmp_path: Path, vfs: LocalVFS) -> None:
    f = tmp_path / "bye.txt"
    f.write_text("gone")

    DeleteCmd([f], vfs).execute()
    assert not f.exists()


