"""Unit tests for TrashCmd."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.commands.trash_cmd import TrashCmd


def test_execute_calls_send2trash(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("data")
    with patch("biome_fm.commands.trash_cmd._send2trash") as mock_trash:
        cmd = TrashCmd([f])
        cmd.execute()
        mock_trash.assert_called_once_with(str(f))


def test_execute_multiple_paths(tmp_path):
    files = [tmp_path / f"f{i}.txt" for i in range(3)]
    for f in files:
        f.write_text("x")
    calls = []
    with patch("biome_fm.commands.trash_cmd._send2trash", side_effect=lambda p: calls.append(p)):
        TrashCmd(files).execute()
    assert calls == [str(f) for f in files]


def test_description_correct(tmp_path):
    files = [tmp_path / "a.txt", tmp_path / "b.txt"]
    cmd = TrashCmd(files)
    assert "2" in cmd.description
    assert "Trash" in cmd.description


def test_description_single():
    cmd = TrashCmd([Path("/x/a.txt")])
    assert "1" in cmd.description or "item" in cmd.description


def test_not_undoable():
    cmd = TrashCmd([Path("/x")])
    assert cmd.undoable is False


def test_undo_is_noop():
    cmd = TrashCmd([Path("/x")])
    cmd.undo()  # should not raise
