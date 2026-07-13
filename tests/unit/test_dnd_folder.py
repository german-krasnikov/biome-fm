"""Tests for DnD folder target detection in ManagerPresenter."""
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


def test_drop_folder_into_itself_blocked(tmp_path):
    """Dragging /a onto /a — silently ignored."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    folder = tmp_path / "folder"
    folder.mkdir()
    m.drop_files([folder], "right", False, target_folder=folder)
    history.execute.assert_not_called()


def test_drop_folder_into_own_subdir_blocked(tmp_path):
    """Dragging /a onto /a/b — silently ignored."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    m.drop_files([parent], "right", False, target_folder=child)
    history.execute.assert_not_called()


def test_drop_mixed_ancestor_and_sibling(tmp_path):
    """Mixed: ancestor blocked, sibling passes through."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir()
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    safe = tmp_path / "safe.txt"
    safe.write_text("x")
    m.drop_files([parent, safe], "right", False, target_folder=child)
    history.execute.assert_called_once()
    cmd = history.execute.call_args[0][0]
    assert safe.resolve() in cmd._sources
    assert parent.resolve() not in cmd._sources
