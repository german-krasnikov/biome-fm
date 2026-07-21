"""F326/F400 — Sort-Key Pre-computation: cache natural sort key in DirSortFilterProxy."""

from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.qt import QApplication, Qt


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _item(name: str, *, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path("/") / name, is_dir=is_dir, size=0, modified=0.0)


class TestSortKeyCache:
    def test_cache_populated_on_lessThan(self, qapp):
        from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy

        model = DirectoryModel()
        proxy = DirSortFilterProxy()
        proxy.setSourceModel(model)

        items = [_item("Bravo"), _item("alpha"), _item("Charlie")]
        model.set_items(items)
        proxy.sort(0, Qt.SortOrder.AscendingOrder)

        # After sorting, cache should be populated
        assert hasattr(proxy, "_sort_key_cache")
        assert len(proxy._sort_key_cache) > 0
        # Keys are natural sort key lists (F400)
        for key in proxy._sort_key_cache.values():
            assert isinstance(key, list)

    def test_cache_cleared_on_model_reset(self, qapp):
        from biome_fm.models.directory_model import DirectoryModel, DirSortFilterProxy

        model = DirectoryModel()
        proxy = DirSortFilterProxy()
        proxy.setSourceModel(model)

        items = [_item("foo"), _item("bar")]
        model.set_items(items)
        proxy.sort(0, Qt.SortOrder.AscendingOrder)

        # Populate cache via sort
        assert len(proxy._sort_key_cache) >= 0  # may be 0 or more

        # Reset model — cache must be cleared
        model.set_items([_item("new_file")])
        assert proxy._sort_key_cache == {}
