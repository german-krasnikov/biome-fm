"""Integration tests for EditorDialog (Feature #18)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from biome_fm.views.editor_dialog import EditorDialog


def test_loads_content(qtbot, tmp_path: Path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("line one\nline two\n")
    dlg = EditorDialog(f)
    qtbot.addWidget(dlg)
    assert "line one" in dlg._editor.toPlainText()
    assert dlg.windowTitle() == "hello.txt"


def test_highlighter_applied_to_python_file(qtbot, tmp_path: Path) -> None:
    f = tmp_path / "test.py"
    f.write_text("def foo(): pass\n")
    dlg = EditorDialog(f)
    qtbot.addWidget(dlg)
    assert dlg._highlighter is not None
    assert dlg._editor.document().characterCount() > 0


def test_ctrl_s_saves(qtbot, tmp_path: Path) -> None:
    f = tmp_path / "save_me.txt"
    f.write_text("original")
    dlg = EditorDialog(f)
    qtbot.addWidget(dlg)
    dlg._editor.setPlainText("updated content")
    saved_paths: list[Path] = []
    dlg.saved.connect(saved_paths.append)
    qtbot.keyClick(dlg, Qt.Key_S, Qt.ControlModifier)
    assert f.read_text() == "updated content"
    assert saved_paths == [f]
