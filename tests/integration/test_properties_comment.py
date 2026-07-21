"""Integration tests for PropertiesDialog comment field."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialogButtonBox, QTextEdit

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.models.file_item import FileItem
from biome_fm.models.finder_tags import get_finder_comment
from biome_fm.views.properties_dialog import PropertiesDialog


def _make_item(path: Path) -> FileItem:
    stat = path.stat()
    return FileItem(
        name=path.name,
        path=path,
        is_dir=False,
        size=stat.st_size,
        modified=stat.st_mtime,
    )


def test_comment_field_exists(qtbot, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    dlg = PropertiesDialog(_make_item(f))
    qtbot.addWidget(dlg)
    te = dlg.findChild(QTextEdit)
    assert te is not None


def test_save_comment_via_ok(qtbot, tmp_path):
    f = tmp_path / "b.txt"
    f.write_text("x")
    dlg = PropertiesDialog(_make_item(f))
    qtbot.addWidget(dlg)

    te = dlg.findChild(QTextEdit)
    te.setPlainText("my comment")

    bbox = dlg.findChild(QDialogButtonBox)
    bbox.accepted.emit()

    assert get_finder_comment(f) == "my comment"
