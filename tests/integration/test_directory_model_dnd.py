"""Tests for DirectoryModel.flags() and ToolTipRole."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem
from biome_fm.qt import Qt


def _item(
    name: str,
    parent: Path = Path("/tmp"),
    *,
    is_dir: bool = False,
    size: int = 100,
    modified: float = 1700000000.0,
) -> FileItem:
    return FileItem(name=name, path=parent / name, is_dir=is_dir, size=size, modified=modified)


@pytest.fixture
def model(qapp):
    return DirectoryModel()


class TestFlags:
    def test_drag_enabled_for_regular_file(self, model):
        model.set_items([_item("foo.txt")])
        flags = model.flags(model.index(0, 0))
        assert flags & Qt.ItemFlag.ItemIsDragEnabled

    def test_drag_disabled_for_dotdot(self, model):
        model.set_items([
            FileItem(name="..", path=Path("/"), is_dir=True, size=0, modified=0.0)
        ])
        flags = model.flags(model.index(0, 0))
        assert not (flags & Qt.ItemFlag.ItemIsDragEnabled)

    def test_drop_enabled_for_all(self, model):
        model.set_items([_item("foo.txt")])
        flags = model.flags(model.index(0, 0))
        assert flags & Qt.ItemFlag.ItemIsDropEnabled

    def test_invalid_index_returns_base_flags(self, model):
        from biome_fm.qt import QModelIndex
        flags = model.flags(QModelIndex())
        # Should not crash and should return some flags
        assert isinstance(flags, Qt.ItemFlag)


class TestToolTip:
    def test_tooltip_contains_path(self, model):
        model.set_items([_item("readme.md")])
        tip = model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole)
        assert "/tmp/readme.md" in tip

    def test_tooltip_contains_size(self, model):
        model.set_items([_item("readme.md", size=512)])
        tip = model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole)
        assert "512" in tip or "B" in tip

    def test_tooltip_contains_modified(self, model):
        model.set_items([_item("readme.md", modified=1700000000.0)])
        tip = model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole)
        assert "2023" in tip  # Nov 2023

    def test_tooltip_dir_no_size(self, model):
        model.set_items([_item("subdir", is_dir=True)])
        tip = model.data(model.index(0, 0), Qt.ItemDataRole.ToolTipRole)
        assert "Size" not in tip

    def test_tooltip_invalid_index_returns_none(self, model):
        from biome_fm.qt import QModelIndex
        tip = model.data(QModelIndex(), Qt.ItemDataRole.ToolTipRole)
        assert tip is None
