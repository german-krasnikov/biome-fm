"""Unit tests for TagStore."""
import tomllib
from pathlib import Path

import pytest

from biome_fm.models.tag_store import TagStore


@pytest.fixture
def store(tmp_path):
    return TagStore.load(tmp_path / "tags.toml")


def test_missing_file_loads_empty(tmp_path):
    s = TagStore.load(tmp_path / "nonexistent.toml")
    assert s.get_tags(Path("/some/file.txt")) == []
    assert s.all_tags() == []


def test_add_and_get_tags(store, tmp_path):
    p = tmp_path / "file.txt"
    store.set_tags(p, ["important", "review"])
    assert store.get_tags(p) == ["important", "review"]


def test_empty_path(store, tmp_path):
    assert store.get_tags(tmp_path / "unknown.txt") == []


def test_tag_color(store):
    store.set_tag_color("important", "#FF0000")
    assert store.tag_color("important") == "#FF0000"
    assert store.tag_color("unknown") is None


def test_all_tags(store, tmp_path):
    store.set_tags(tmp_path / "a.txt", ["zebra", "alpha"])
    store.set_tags(tmp_path / "b.txt", ["alpha", "beta"])
    assert store.all_tags() == ["alpha", "beta", "zebra"]


def test_paths_for_tag(store, tmp_path):
    a, b, c = tmp_path / "a.txt", tmp_path / "b.txt", tmp_path / "c.txt"
    store.set_tags(a, ["work"])
    store.set_tags(b, ["work", "urgent"])
    store.set_tags(c, ["personal"])
    result = store.paths_for_tag("work")
    assert set(result) == {a, b}


def test_toml_roundtrip(tmp_path):
    path = tmp_path / "tags.toml"
    s = TagStore.load(path)
    f = tmp_path / "file.txt"
    s.set_tags(f, ["alpha", "beta"])
    s.set_tag_color("alpha", "#AABBCC")
    s.save()

    s2 = TagStore.load(path)
    assert s2.get_tags(f) == ["alpha", "beta"]
    assert s2.tag_color("alpha") == "#AABBCC"
