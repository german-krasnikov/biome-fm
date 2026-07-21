"""F443 — Content Plugin Columns: unit tests (no Qt)."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.plugins.hookspecs import BiomeFMSpec
from biome_fm.plugins.types import ColumnDef


# ---------------------------------------------------------------------------
# Mock plugin manager
# ---------------------------------------------------------------------------

class MockHook:
    def extra_columns(self):
        return [[ColumnDef(id="test.col", title="Test")]]

    def column_value(self, item, column_id):
        return "value1" if column_id == "test.col" else None


class MockPM:
    hook = MockHook()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_column_value_hookspec_exists():
    assert hasattr(BiomeFMSpec, "column_value")


def test_directory_model_extra_columns(qtbot):
    from biome_fm.models.directory_model import DirectoryModel, HEADERS
    m = DirectoryModel()
    m.set_plugin_manager(MockPM())
    assert m.columnCount() == len(HEADERS) + 1
    assert m.headerData(len(HEADERS), __import__("biome_fm.qt", fromlist=["Qt"]).Qt.Orientation.Horizontal) == "Test"


def test_directory_model_plugin_data(qtbot):
    from biome_fm.models.directory_model import DirectoryModel, HEADERS
    from biome_fm.models.file_item import FileItem
    m = DirectoryModel()
    m.set_plugin_manager(MockPM())
    item = FileItem(name="foo.txt", path=Path("/tmp/foo.txt"), is_dir=False, size=0, modified=0.0)
    m.set_items([item])
    idx = m.index(0, len(HEADERS))
    assert m.data(idx) == "value1"
