"""Unit tests for DirectoryModel ToolTipRole."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem


def _file(name: str, *, size: int = 1024, modified: float = 1_700_000_000.0) -> FileItem:
    return FileItem(name=name, path=Path("/tmp") / name, is_dir=False, size=size, modified=modified)


def _dotdot() -> FileItem:
    return FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0)


def _tooltip(model: DirectoryModel, row: int = 0) -> str | None:
    return model.data(model.index(row, 0), Qt.ItemDataRole.ToolTipRole)


def test_tooltip_shows_path(qtbot) -> None:
    m = DirectoryModel()
    m.set_items([_file("report.pdf")])
    tip = _tooltip(m)
    assert "/tmp/report.pdf" in tip


def test_tooltip_shows_size(qtbot) -> None:
    m = DirectoryModel()
    m.set_items([_file("data.csv", size=2048)])
    tip = _tooltip(m)
    assert "2.0 KB" in tip


def test_dotdot_no_tooltip(qtbot) -> None:
    m = DirectoryModel()
    m.set_items([_dotdot()])
    tip = _tooltip(m)
    assert not tip  # empty string or None
