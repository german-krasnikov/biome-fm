"""Tests for EditorRenameCmd."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS


class _SpyVFS:
    def __init__(self, exists_for: set[str] | None = None) -> None:
        self.calls: list[tuple] = []
        self._exists_for: set[str] = exists_for or set()

    def exists(self, path: Path) -> bool:
        return path.name in self._exists_for

    def move(self, src: Path, dst: Path) -> None:
        self.calls.append(("move", src, dst))

    def listdir(self, path: Path) -> list:
        return []

    def mkdir(self, path: Path) -> None:
        self.calls.append(("mkdir", path))

    def copy(self, src: Path, dst: Path) -> None:
        self.calls.append(("copy", src, dst))

    def delete(self, path: Path) -> None:
        self.calls.append(("delete", path))


def _item(tmp_path: Path, name: str) -> FileItem:
    p = tmp_path / name
    p.write_text("x")
    return FileItem(name=name, path=p, is_dir=False, size=1, modified=0.0)


def _editor_that_renames(mapping: dict[str, str]):
    """Returns an editor fn that replaces names in the temp file per mapping."""
    def _edit(tmp_file: Path) -> None:
        lines = tmp_file.read_text().splitlines()
        new_lines = [mapping.get(line, line) for line in lines]
        tmp_file.write_text("\n".join(new_lines) + "\n")
    return _edit


def test_renames_changed_lines(tmp_path: Path) -> None:
    from biome_fm.commands.editor_rename_cmd import EditorRenameCmd

    a = _item(tmp_path, "a.txt")
    b = _item(tmp_path, "b.txt")
    vfs = LocalVFS()
    cmd = EditorRenameCmd([a, b], vfs, editor=_editor_that_renames({"a.txt": "renamed_a.txt"}))
    cmd.execute()

    assert (tmp_path / "renamed_a.txt").exists()
    assert (tmp_path / "b.txt").exists()  # unchanged


def test_unchanged_skipped(tmp_path: Path) -> None:
    from biome_fm.commands.editor_rename_cmd import EditorRenameCmd

    a = _item(tmp_path, "keep.txt")
    vfs = LocalVFS()
    cmd = EditorRenameCmd([a], vfs, editor=_editor_that_renames({}))
    cmd.execute()

    assert (tmp_path / "keep.txt").exists()


def test_editor_rename_raises_on_line_count_mismatch(tmp_path: Path) -> None:
    """Editor deletes one line → ValueError before any FS mutation."""
    from biome_fm.commands.editor_rename_cmd import EditorRenameCmd

    a = _item(tmp_path, "a.txt")
    b = _item(tmp_path, "b.txt")
    spy = _SpyVFS()

    def _delete_one_line(tmp_file: Path) -> None:
        lines = tmp_file.read_text().splitlines()
        tmp_file.write_text(lines[0] + "\n")  # write only first line

    cmd = EditorRenameCmd([a, b], spy, editor=_delete_one_line)
    with pytest.raises(ValueError, match="Line count changed"):
        cmd.execute()

    assert spy.calls == []


def test_editor_rename_raises_before_any_rename_when_second_target_exists(
    tmp_path: Path,
) -> None:
    """Pre-check fires before any move when second target already exists."""
    from biome_fm.commands.editor_rename_cmd import EditorRenameCmd

    a = _item(tmp_path, "a.txt")
    b = _item(tmp_path, "b.txt")
    # spy reports that "b_new.txt" already exists
    spy = _SpyVFS(exists_for={"b_new.txt"})

    def _rename_both(tmp_file: Path) -> None:
        tmp_file.write_text("a_new.txt\nb_new.txt\n")

    cmd = EditorRenameCmd([a, b], spy, editor=_rename_both)
    with pytest.raises(FileExistsError):
        cmd.execute()

    # move must not be called even for the first item
    assert spy.calls == []
