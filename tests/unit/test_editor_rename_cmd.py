"""Tests for EditorRenameCmd."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS


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

    assert len(cmd._sub_cmds) == 0
    assert (tmp_path / "keep.txt").exists()


def test_undo_restores(tmp_path: Path) -> None:
    from biome_fm.commands.editor_rename_cmd import EditorRenameCmd

    a = _item(tmp_path, "orig.txt")
    vfs = LocalVFS()
    cmd = EditorRenameCmd([a], vfs, editor=_editor_that_renames({"orig.txt": "new.txt"}))
    cmd.execute()
    assert (tmp_path / "new.txt").exists()

    cmd.undo()
    assert (tmp_path / "orig.txt").exists()
    assert not (tmp_path / "new.txt").exists()
