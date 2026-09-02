"""Tests for DnD folder target detection in ManagerPresenter."""
from unittest.mock import MagicMock

from biome_fm.presenters.manager_presenter import ManagerPresenter


def test_drop_files_uses_target_folder(tmp_path):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    m = ManagerPresenter(left, right, vfs)
    target = tmp_path / "right" / "subfolder"
    target.mkdir()
    src = tmp_path / "file.txt"
    src.write_text("data")
    m.drop_files([src], "right", False, target_folder=target)
    vfs.copy.assert_called_once_with(src.resolve(), target / "file.txt")


def test_drop_files_no_folder_uses_pane_path(tmp_path):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    m = ManagerPresenter(left, right, vfs)
    src = tmp_path / "file.txt"
    src.write_text("data")
    m.drop_files([src], "right", False, target_folder=None)
    vfs.copy.assert_called_once_with(src.resolve(), (tmp_path / "right") / "file.txt")


def test_drop_folder_into_itself_blocked(tmp_path):
    """Dragging /a onto /a — silently ignored."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    m = ManagerPresenter(left, right, vfs)
    folder = tmp_path / "folder"
    folder.mkdir()
    m.drop_files([folder], "right", False, target_folder=folder)
    vfs.copy.assert_not_called()


def test_drop_folder_into_own_subdir_blocked(tmp_path):
    """Dragging /a onto /a/b — silently ignored."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    m = ManagerPresenter(left, right, vfs)
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    m.drop_files([parent], "right", False, target_folder=child)
    vfs.copy.assert_not_called()


def test_drop_mixed_ancestor_and_sibling(tmp_path):
    """Mixed: ancestor blocked, sibling passes through."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    m = ManagerPresenter(left, right, vfs)
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    safe = tmp_path / "safe.txt"
    safe.write_text("x")
    m.drop_files([parent, safe], "right", False, target_folder=child)
    vfs.copy.assert_called_once()
    assert vfs.copy.call_args[0][0] == safe.resolve()
