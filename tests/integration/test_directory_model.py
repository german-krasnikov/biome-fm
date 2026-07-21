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

    def test_column_count_is_6(self, model):
        assert model.columnCount() == 6

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


class TestSymlinkDisplay:
    def test_symlink_name_shows_target(self, qapp):
        model = DirectoryModel()
        item = FileItem(
            name="link", path=Path("link"), is_dir=False, size=0, modified=0.0,
            is_symlink=True, symlink_target=Path("/target/path"),
        )
        model.set_items([item])
        assert model.data(model.index(0, COL_NAME)) == "link → /target/path"

    def test_regular_file_name_unchanged(self, qapp):
        model = DirectoryModel()
        item = FileItem(name="file.txt", path=Path("file.txt"), is_dir=False, size=0, modified=0.0)
        model.set_items([item])
        assert model.data(model.index(0, COL_NAME)) == "file.txt"

    def test_broken_symlink_foreground_red(self, qapp, tmp_path):
        from biome_fm.qt import QBrush, QColor
        model = DirectoryModel()
        broken = tmp_path / "dead_link"
        # path doesn't exist → broken symlink
        item = FileItem(
            name="dead_link", path=broken, is_dir=False, size=0, modified=0.0,
            is_symlink=True, symlink_target=Path("/nonexistent"), is_broken=True,
        )
        model.set_items([item])
        role = Qt.ItemDataRole.ForegroundRole
        brush = model.data(model.index(0, COL_NAME), role)
        assert isinstance(brush, QBrush)
        assert brush.color() == QColor("#cc3333")

    def test_valid_symlink_not_red(self, qapp, tmp_path):
        from biome_fm.qt import QBrush
        model = DirectoryModel()
        real = tmp_path / "real.txt"
        real.write_text("x")
        item = FileItem(
            name="real.txt", path=real, is_dir=False, size=1, modified=0.0,
            is_symlink=True, symlink_target=Path("/somewhere/real.txt"),
        )
        model.set_items([item])
        role = Qt.ItemDataRole.ForegroundRole
        brush = model.data(model.index(0, COL_NAME), role)
        # Should not be the broken-link red
        from biome_fm.qt import QColor
        if isinstance(brush, QBrush):
            assert brush.color() != QColor("#cc3333")


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
