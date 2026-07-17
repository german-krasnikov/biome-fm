"""Unit tests for DirectoryModel git status coloring."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem


def _file(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=False, size=0, modified=0.0)


def _dir(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=True, size=0, modified=0.0)


def _fg(model: DirectoryModel, row: int = 0) -> QBrush | None:
    return model.data(model.index(row, 0), Qt.ItemDataRole.ForegroundRole)


def test_set_git_status_modified_foreground(qtbot):
    p = Path("/repo/foo.py")
    m = DirectoryModel()
    m.set_items([_file(p)])
    m.set_git_status({p: " M"}, frozenset())
    brush = _fg(m)
    assert isinstance(brush, QBrush)
    assert brush.color().name().lower() == "#e69f00"


def test_set_git_status_added_foreground(qtbot):
    p = Path("/repo/new.py")
    m = DirectoryModel()
    m.set_items([_file(p)])
    m.set_git_status({p: "A "}, frozenset())
    brush = _fg(m)
    assert isinstance(brush, QBrush)
    assert brush.color().name().lower() == "#009e73"


def test_set_git_status_untracked_foreground(qtbot):
    p = Path("/repo/untracked.txt")
    m = DirectoryModel()
    m.set_items([_file(p)])
    m.set_git_status({p: "??"}, frozenset())
    brush = _fg(m)
    assert isinstance(brush, QBrush)
    assert brush.color().name().lower() == "#808080"


def test_set_git_status_dirty_dir(qtbot):
    p = Path("/repo/src")
    m = DirectoryModel()
    m.set_items([_dir(p)])
    m.set_git_status({}, frozenset([p]))
    brush = _fg(m)
    assert isinstance(brush, QBrush)
    assert brush.color().name().lower() == "#e69f00"


def test_set_git_status_clean_file_no_git_color(qtbot):
    p = Path("/repo/clean.xyz")  # unknown extension → no ext or git color
    m = DirectoryModel()
    m.set_items([_file(p)])
    m.set_git_status({}, frozenset())
    result = _fg(m)
    assert result is None


def test_set_git_status_emits_data_changed(qtbot):
    p = Path("/repo/foo.py")
    m = DirectoryModel()
    m.set_items([_file(p)])
    signals: list[list[Qt.ItemDataRole]] = []
    m.dataChanged.connect(lambda tl, br, roles: signals.append(roles))
    m.set_git_status({p: " M"}, frozenset())
    assert signals
    assert Qt.ItemDataRole.ForegroundRole in signals[0]
