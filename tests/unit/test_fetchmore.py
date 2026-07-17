"""Unit tests for DirectoryModel fetchMore / canFetchMore lazy loading."""
from pathlib import Path

from biome_fm.models.directory_model import DirectoryModel
from biome_fm.models.file_item import FileItem


def _item(name: str) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=0, modified=0.0)


def test_initial_batch_limited(qapp):
    model = DirectoryModel()
    items = [_item(f"file_{i:04d}.txt") for i in range(500)]
    model.set_items(items)
    assert model.rowCount() == 200
    assert model.canFetchMore()


def test_fetch_loads_more(qapp):
    model = DirectoryModel()
    items = [_item(f"file_{i:04d}.txt") for i in range(500)]
    model.set_items(items)
    before = model.rowCount()
    model.fetchMore()
    assert model.rowCount() == before + 200


def test_small_dir_no_fetch(qapp):
    model = DirectoryModel()
    items = [_item(f"file_{i}.txt") for i in range(10)]
    model.set_items(items)
    assert model.rowCount() == 10
    assert not model.canFetchMore()
