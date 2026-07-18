"""Integration tests for BatchRenameDialog (TDD — red phase)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialogButtonBox

from biome_fm.models.file_item import FileItem
from biome_fm.views.batch_rename_dialog import BatchRenameDialog


def _items(tmp_path: Path, names: list[str]) -> list[FileItem]:
    return [FileItem(n, tmp_path / n, False, 0, 0.0) for n in names]


def test_dialog_has_widgets(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["a.txt", "b.txt"]))
    qtbot.addWidget(dlg)
    assert dlg._find is not None
    assert dlg._replace is not None
    assert dlg._regex is not None
    assert dlg._table.columnCount() == 2


def test_typing_find_updates_preview(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["foo.txt", "bar.txt"]))
    qtbot.addWidget(dlg)
    dlg._find.setText("foo")
    dlg._replace.setText("baz")
    assert dlg._table.rowCount() == 2
    assert dlg._table.item(0, 1).text() == "baz.txt"
    assert dlg._table.item(1, 1).text() == "bar.txt"  # unchanged, no match


def test_collision_rows_red(qtbot, tmp_path: Path) -> None:
    # Both files rename to same name → conflict → red background
    dlg = BatchRenameDialog(_items(tmp_path, ["ac.txt", "bc.txt"]))
    qtbot.addWidget(dlg)
    dlg._regex.setChecked(True)
    dlg._find.setText("[ab]c")
    dlg._replace.setText("x")
    # "ac.txt" → "x.txt", "bc.txt" → "x.txt" — collision
    r0 = dlg._table.item(0, 1).background().color()
    r1 = dlg._table.item(1, 1).background().color()
    assert r0 == QColor("#ff6b6b")
    assert r1 == QColor("#ff6b6b")


def test_renames_excludes_conflicts(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["ac.txt", "bc.txt"]))
    qtbot.addWidget(dlg)
    dlg._regex.setChecked(True)
    dlg._find.setText("[ab]c")
    dlg._replace.setText("x")
    assert dlg.renames == []


def test_ok_disabled_when_find_empty(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["a.txt"]))
    qtbot.addWidget(dlg)
    ok = dlg._bbox.button(QDialogButtonBox.StandardButton.Ok)
    # empty find → disabled
    assert not ok.isEnabled()
    # find with no match → still disabled
    dlg._find.setText("z")
    assert not ok.isEnabled()
    # valid rename → enabled
    dlg._find.setText("a")
    dlg._replace.setText("b")
    assert ok.isEnabled()


def test_regex_mode(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["file_001.txt", "file_002.txt"]))
    qtbot.addWidget(dlg)
    dlg._regex.setChecked(True)
    dlg._find.setText(r"_(\d+)")
    dlg._replace.setText(r"_v\1")
    assert dlg._table.item(0, 1).text() == "file_v001.txt"
    assert dlg._table.item(1, 1).text() == "file_v002.txt"
    assert len(dlg.renames) == 2


def test_case_sensitive_checkbox_exists(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["Foo.txt", "foo.txt"]))
    qtbot.addWidget(dlg)
    assert hasattr(dlg, "_case")
    assert dlg._case.isChecked()  # default: case-sensitive


def test_case_insensitive_renames_both(qtbot, tmp_path: Path) -> None:
    dlg = BatchRenameDialog(_items(tmp_path, ["Foo.txt", "foo.txt"]))
    qtbot.addWidget(dlg)
    dlg._case.setChecked(False)  # case-insensitive
    dlg._find.setText("foo")
    dlg._replace.setText("bar")
    assert dlg._table.item(0, 1).text() == "bar.txt"
    assert dlg._table.item(1, 1).text() == "bar.txt"
