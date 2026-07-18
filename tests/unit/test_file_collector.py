"""Unit tests for FileCollector."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str, parent: str = "/a") -> FileItem:
    p = Path(parent) / name
    return FileItem(name=name, path=p, is_dir=False, size=100, modified=0.0)


@pytest.fixture
def collector():
    from biome_fm.presenters.file_collector import FileCollector
    return FileCollector()


def test_add_items(collector) -> None:
    collector.add([_item("foo.txt"), _item("bar.txt")])
    assert collector.count() == 2


def test_add_deduplicates(collector) -> None:
    item = _item("foo.txt")
    collector.add([item, item])
    assert collector.count() == 1


def test_remove_items(collector) -> None:
    a = _item("a.txt")
    b = _item("b.txt")
    collector.add([a, b])
    collector.remove([a.path])
    assert collector.count() == 1
    assert collector.items()[0].path == b.path


def test_clear(collector) -> None:
    collector.add([_item("x.txt"), _item("y.txt")])
    collector.clear()
    assert collector.count() == 0


def test_items_returns_copy(collector) -> None:
    collector.add([_item("z.txt")])
    lst = collector.items()
    lst.clear()
    assert collector.count() == 1
