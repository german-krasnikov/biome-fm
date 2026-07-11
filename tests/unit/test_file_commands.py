"""Unit tests for file commands (no real FS except MkdirCmd)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.commands.copy_cmd import CopyCmd
from biome_fm.commands.delete_cmd import DeleteCmd
from biome_fm.commands.mkdir_cmd import MkdirCmd
from biome_fm.commands.move_cmd import MoveCmd
from biome_fm.commands.rename_cmd import RenameCmd


class SpyVFS:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def copy(self, src: Path, dst: Path) -> None:
        self.calls.append(("copy", src, dst))

    def move(self, src: Path, dst: Path) -> None:
        self.calls.append(("move", src, dst))

    def delete(self, path: Path) -> None:
        self.calls.append(("delete", path))

    def mkdir(self, path: Path) -> None:
        self.calls.append(("mkdir", path))

    def exists(self, path: Path) -> bool:
        return False

    def listdir(self, path: Path) -> list:
        return []

    def stat(self, path: Path) -> None:  # type: ignore[return]
        ...


# --- DeleteCmd ---

def test_delete_calls_vfs_delete_for_each_path() -> None:
    vfs = SpyVFS()
    paths = [Path("/a/b"), Path("/a/c")]
    DeleteCmd(paths, vfs).execute()
    assert vfs.calls == [("delete", Path("/a/b")), ("delete", Path("/a/c"))]


def test_delete_not_undoable() -> None:
    assert DeleteCmd([Path("/x")], SpyVFS()).undoable is False


def test_delete_undo_is_noop() -> None:
    vfs = SpyVFS()
    cmd = DeleteCmd([Path("/x")], vfs)
    cmd.undo()
    assert vfs.calls == []


def test_delete_description_single() -> None:
    assert DeleteCmd([Path("/x")], SpyVFS()).description == "Delete 1 item"


def test_delete_description_plural() -> None:
    assert DeleteCmd([Path("/a"), Path("/b")], SpyVFS()).description == "Delete 2 items"


# --- MkdirCmd ---

def test_mkdir_invalid_name_raises() -> None:
    # backslash is a Windows path separator — rejected as invalid directory name
    with pytest.raises(ValueError):
        MkdirCmd(Path("/a") / "foo\\bar", SpyVFS())


def test_mkdir_execute_creates_dir(tmp_path: Path) -> None:
    target = tmp_path / "newdir"
    MkdirCmd(target, SpyVFS()).execute()
    assert target.is_dir()


def test_mkdir_undo_removes_dir(tmp_path: Path) -> None:
    target = tmp_path / "newdir"
    cmd = MkdirCmd(target, SpyVFS())
    cmd.execute()
    cmd.undo()
    assert not target.exists()


def test_mkdir_undo_noop_if_not_exists(tmp_path: Path) -> None:
    # Should not raise even if dir was never created
    cmd = MkdirCmd(tmp_path / "ghost", SpyVFS())
    cmd.undo()  # no error


def test_mkdir_description() -> None:
    assert MkdirCmd(Path("/a/mydir"), SpyVFS()).description == "Create folder 'mydir'"


def test_mkdir_undoable() -> None:
    assert MkdirCmd(Path("/a/mydir"), SpyVFS()).undoable is True


# --- RenameCmd ---

def test_rename_invalid_name_with_slash_raises() -> None:
    with pytest.raises(ValueError):
        RenameCmd(Path("/a/foo.txt"), "sub/bar.txt", SpyVFS())


def test_rename_execute_calls_move() -> None:
    vfs = SpyVFS()
    RenameCmd(Path("/a/foo.txt"), "bar.txt", vfs).execute()
    assert vfs.calls == [("move", Path("/a/foo.txt"), Path("/a/bar.txt"))]


def test_rename_undo_calls_move_back() -> None:
    vfs = SpyVFS()
    cmd = RenameCmd(Path("/a/foo.txt"), "bar.txt", vfs)
    cmd.execute()
    vfs.calls.clear()
    cmd.undo()
    assert vfs.calls == [("move", Path("/a/bar.txt"), Path("/a/foo.txt"))]


def test_rename_description() -> None:
    cmd = RenameCmd(Path("/a/foo.txt"), "bar.txt", SpyVFS())
    assert cmd.description == "Rename 'foo.txt' → 'bar.txt'"


def test_rename_undoable() -> None:
    assert RenameCmd(Path("/a/foo.txt"), "bar.txt", SpyVFS()).undoable is True


# --- CopyCmd ---

def test_copy_execute_calls_vfs_copy() -> None:
    vfs = SpyVFS()
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    CopyCmd(sources, Path("/dst"), vfs).execute()
    assert vfs.calls == [
        ("copy", Path("/src/a.txt"), Path("/dst/a.txt")),
        ("copy", Path("/src/b.txt"), Path("/dst/b.txt")),
    ]


def test_copy_tracks_created_paths() -> None:
    vfs = SpyVFS()
    cmd = CopyCmd([Path("/src/a.txt")], Path("/dst"), vfs)
    cmd.execute()
    assert cmd._created == [Path("/dst/a.txt")]


def test_copy_undo_deletes_created_in_reverse() -> None:
    vfs = SpyVFS()
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    cmd = CopyCmd(sources, Path("/dst"), vfs)
    cmd.execute()
    vfs.calls.clear()
    cmd.undo()
    assert vfs.calls == [
        ("delete", Path("/dst/b.txt")),
        ("delete", Path("/dst/a.txt")),
    ]


def test_copy_undo_clears_created() -> None:
    vfs = SpyVFS()
    cmd = CopyCmd([Path("/src/a.txt")], Path("/dst"), vfs)
    cmd.execute()
    cmd.undo()
    assert cmd._created == []


def test_copy_description_single() -> None:
    assert CopyCmd([Path("/src/a.txt")], Path("/dst"), SpyVFS()).description == "Copy 1 item"


def test_copy_description_plural() -> None:
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    assert CopyCmd(sources, Path("/dst"), SpyVFS()).description == "Copy 2 items"


def test_copy_undoable() -> None:
    assert CopyCmd([Path("/src/a.txt")], Path("/dst"), SpyVFS()).undoable is True


# --- MoveCmd ---

def test_move_execute_calls_vfs_move() -> None:
    vfs = SpyVFS()
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    MoveCmd(sources, Path("/dst"), vfs).execute()
    assert vfs.calls == [
        ("move", Path("/src/a.txt"), Path("/dst/a.txt")),
        ("move", Path("/src/b.txt"), Path("/dst/b.txt")),
    ]


def test_move_tracks_moves() -> None:
    vfs = SpyVFS()
    cmd = MoveCmd([Path("/src/a.txt")], Path("/dst"), vfs)
    cmd.execute()
    assert cmd._moves == [(Path("/src/a.txt"), Path("/dst/a.txt"))]


def test_move_undo_moves_back_in_reverse() -> None:
    vfs = SpyVFS()
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    cmd = MoveCmd(sources, Path("/dst"), vfs)
    cmd.execute()
    vfs.calls.clear()
    cmd.undo()
    assert vfs.calls == [
        ("move", Path("/dst/b.txt"), Path("/src/b.txt")),
        ("move", Path("/dst/a.txt"), Path("/src/a.txt")),
    ]


def test_move_undo_clears_moves() -> None:
    vfs = SpyVFS()
    cmd = MoveCmd([Path("/src/a.txt")], Path("/dst"), vfs)
    cmd.execute()
    cmd.undo()
    assert cmd._moves == []


def test_move_description_single() -> None:
    assert MoveCmd([Path("/src/a.txt")], Path("/dst"), SpyVFS()).description == "Move 1 item"


def test_move_description_plural() -> None:
    sources = [Path("/src/a.txt"), Path("/src/b.txt")]
    assert MoveCmd(sources, Path("/dst"), SpyVFS()).description == "Move 2 items"


def test_move_undoable() -> None:
    assert MoveCmd([Path("/src/a.txt")], Path("/dst"), SpyVFS()).undoable is True
