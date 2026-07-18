"""TDD: TagCmd — batch tag assign/remove with undo. F283."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.tag_store import TagStore
from biome_fm.commands.tag_cmd import TagCmd


@pytest.fixture
def store(tmp_path):
    return TagStore.load(tmp_path / "tags.toml")


def test_execute_adds_tags(store, tmp_path):
    paths = [tmp_path / "a.txt", tmp_path / "b.txt"]
    cmd = TagCmd(paths, add_tags=["Work"], remove_tags=[], store=store)
    cmd.execute()
    assert "Work" in store.get_tags(paths[0])
    assert "Work" in store.get_tags(paths[1])


def test_undo_restores(store, tmp_path):
    p = tmp_path / "a.txt"
    store.set_tags(p, ["Old"])
    cmd = TagCmd([p], add_tags=["New"], remove_tags=[], store=store)
    cmd.execute()
    assert "New" in store.get_tags(p)
    cmd.undo()
    assert store.get_tags(p) == ["Old"]


def test_remove_tags(store, tmp_path):
    p = tmp_path / "a.txt"
    store.set_tags(p, ["Keep", "Remove"])
    cmd = TagCmd([p], add_tags=[], remove_tags=["Remove"], store=store)
    cmd.execute()
    tags = store.get_tags(p)
    assert "Keep" in tags
    assert "Remove" not in tags
