"""Integration tests for DirectoryModel + DirSortFilterProxy (requires Qt)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from biome_fm.models.directory_model import COL_NAME, COL_SIZE, DirectoryModel, DirSortFilterProxy
from biome_fm.models.file_item import FileItem
from biome_fm.qt import Qt


def _item(name: str, *, is_dir: bool = False, size: int = 0) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=is_dir, size=size, modified=0.0)


@pytest.fixture
def model(qapp):
    return DirectoryModel()


@pytest.fixture
def items():
    return [
        _item("..", is_dir=True),
        _item("docs", is_dir=True),
        _item("readme.txt", size=1024),
        _item("notes.md", size=30),
    ]


class TestDirectoryModel:
    def test_initial_row_count_zero(self, model):
        assert model.rowCount() == 0

    def test_set_items_updates_row_count(self, model, items):
        model.set_items(items)
        assert model.rowCount() == len(items)

    def test_column_count_is_4(self, model):
        assert model.columnCount() == 4

    def test_data_name_column(self, model, items):
        model.set_items(items)
        idx = model.index(1, COL_NAME)
        assert model.data(idx) == "docs"

    def test_data_size_column_dir(self, model, items):
        model.set_items(items)
        idx = model.index(1, COL_SIZE)
        assert model.data(idx) == "<DIR>"

    def test_data_size_column_file(self, model, items):
        model.set_items(items)
        # readme.txt is at row 2, size=1024 → "1.0 KB"
        idx = model.index(2, COL_SIZE)
        assert model.data(idx) == "1.0 KB"

    def test_data_userrole_returns_fileitem(self, model, items):
        model.set_items(items)
        idx = model.index(0, COL_NAME)
        result = model.data(idx, Qt.ItemDataRole.UserRole)
        assert isinstance(result, FileItem)
        assert result.name == ".."

    def test_header_data(self, model):
        for col, expected in enumerate(("Name", "Size", "Modified", "Ext")):
            assert model.headerData(col, Qt.Orientation.Horizontal) == expected

    def test_set_items_empty_list(self, model, items):
        model.set_items(items)
        model.set_items([])
        assert model.rowCount() == 0

    def test_invalid_index_returns_none(self, model, items):
        model.set_items(items)
        assert model.data(model.index(99, 0)) is None


class TestDirSortFilterProxy:
    def test_proxy_sorts_dirs_first(self, qapp):
        model = DirectoryModel()
        proxy = DirSortFilterProxy()
        proxy.setSourceModel(model)
        items = [
            _item("zebra.txt"),
            _item("alpha", is_dir=True),
            _item("..", is_dir=True),
        ]
        model.set_items(items)
        proxy.sort(COL_NAME, Qt.SortOrder.AscendingOrder)
        first = proxy.data(proxy.index(0, COL_NAME))
        second = proxy.data(proxy.index(1, COL_NAME))
        assert first == ".."
        assert second == "alpha"
