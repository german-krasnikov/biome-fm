"""TDD: Background file indexer with SQLite FTS5."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def indexer(tmp_path):
    from biome_fm.models.file_indexer import FileIndexer

    return FileIndexer(tmp_path / "idx.db")


def test_search_empty(indexer) -> None:
    results = indexer.search("nothing")
    assert results == []


def test_index_and_search(qtbot, tmp_path, indexer) -> None:
    (tmp_path / "hello_world.txt").touch()
    (tmp_path / "readme.md").touch()

    with qtbot.waitSignal(indexer.indexing_done, timeout=3000):
        indexer.index_dir(tmp_path)

    results = indexer.search("hello")
    assert any("hello_world.txt" in str(p) for p in results)


def test_reindex_updates(qtbot, tmp_path, indexer) -> None:
    (tmp_path / "old.txt").touch()

    with qtbot.waitSignal(indexer.indexing_done, timeout=3000):
        indexer.index_dir(tmp_path)

    assert any("old.txt" in str(p) for p in indexer.search("old"))

    # Add a new file and reindex
    (tmp_path / "new_file.py").touch()
    with qtbot.waitSignal(indexer.indexing_done, timeout=3000):
        indexer.index_dir(tmp_path)

    assert any("new_file" in str(p) for p in indexer.search("new_file"))
