"""Tests for DnD folder target detection in ManagerPresenter."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.presenters.manager_presenter import ManagerPresenter


def test_drop_files_uses_target_folder(tmp_path):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    target = tmp_path / "right" / "subfolder"
    target.mkdir()
    src = tmp_path / "file.txt"
    src.write_text("data")
    m.drop_files([src], "right", False, target_folder=target)
    cmd = history.execute.call_args[0][0]
    assert cmd._dest_dir == target


def test_drop_files_no_folder_uses_pane_path(tmp_path):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    src = tmp_path / "file.txt"
    src.write_text("data")
    m.drop_files([src], "right", False, target_folder=None)
    cmd = history.execute.call_args[0][0]
    assert cmd._dest_dir == tmp_path / "right"
