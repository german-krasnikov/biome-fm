"""Unit tests for inline rename delegate and DirectoryModel flags."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QLineEdit

from biome_fm.models.directory_model import COL_NAME, DirectoryModel
from biome_fm.models.file_item import FileItem
from biome_fm.qt import Qt
from biome_fm.views.pane_view import PaneView, _DropHintDelegate


def _item(name: str, is_dir: bool = False) -> FileItem:
    path = Path("/tmp") / name
    return FileItem(name=name, path=path, is_dir=is_dir, size=0, modified=0.0)


def _make_pane(qtbot, items):
    pane = PaneView()
    qtbot.addWidget(pane)
    pane._model.set_items(items)
    return pane


# ── DirectoryModel.flags ──────────────────────────────────────────────────────

def test_flags_col0_non_dotdot_is_editable(qtbot):
    """Column 0 of a regular item must have ItemIsEditable."""
    model = DirectoryModel()
    model.set_items([_item("file.txt")])
    idx = model.index(0, COL_NAME)
    assert model.flags(idx) & Qt.ItemFlag.ItemIsEditable


def test_flags_dotdot_not_editable(qtbot):
    """'..' row must NOT be editable."""
    model = DirectoryModel()
    model.set_items([_item("..")])
    idx = model.index(0, COL_NAME)
    assert not (model.flags(idx) & Qt.ItemFlag.ItemIsEditable)


def test_flags_col1_not_editable(qtbot):
    """Size column (col 1) is never editable."""
    model = DirectoryModel()
    model.set_items([_item("file.txt")])
    idx = model.index(0, 1)
    assert not (model.flags(idx) & Qt.ItemFlag.ItemIsEditable)


# ── _DropHintDelegate editing ─────────────────────────────────────────────────

def test_create_editor_none_for_dotdot(qtbot):
    pane = _make_pane(qtbot, [_item("..")])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)
    assert delegate.createEditor(pane._table, None, idx) is None


def test_create_editor_returns_line_edit_with_name(qtbot):
    pane = _make_pane(qtbot, [_item("notes.txt")])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)
    editor = delegate.createEditor(pane._table, None, idx)
    assert isinstance(editor, QLineEdit)
    assert editor.text() == "notes.txt"


def test_create_editor_stem_selection_for_file(qtbot):
    """For 'photo.jpg', selection should cover only 'photo' (0..5)."""
    pane = _make_pane(qtbot, [_item("photo.jpg")])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)
    editor = delegate.createEditor(pane._table, None, idx)
    sel_start = editor.selectionStart()
    sel_len = editor.selectionLength()
    assert sel_start == 0
    assert sel_len == len("photo")  # not including '.jpg'


def test_create_editor_full_selection_for_directory(qtbot):
    pane = _make_pane(qtbot, [_item("my_folder", is_dir=True)])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)
    editor = delegate.createEditor(pane._table, None, idx)
    assert editor.selectionLength() == len("my_folder")


def test_set_model_data_emits_signal(qtbot):
    pane = _make_pane(qtbot, [_item("old.txt")])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)

    signals = []
    pane.inline_rename_requested.connect(lambda i, n: signals.append((i, n)))

    editor = QLineEdit()
    editor.setText("new.txt")
    delegate.setModelData(editor, pane._proxy, idx)
    assert len(signals) == 1
    assert signals[0][1] == "new.txt"


def test_set_model_data_skips_emit_when_unchanged(qtbot):
    pane = _make_pane(qtbot, [_item("same.txt")])
    delegate: _DropHintDelegate = pane._table.itemDelegate()
    idx = pane._proxy.index(0, 0)

    signals = []
    pane.inline_rename_requested.connect(lambda i, n: signals.append((i, n)))

    editor = QLineEdit()
    editor.setText("same.txt")
    delegate.setModelData(editor, pane._proxy, idx)
    assert signals == []
