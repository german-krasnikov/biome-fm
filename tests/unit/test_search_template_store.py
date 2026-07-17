"""Unit tests for SearchTemplateStore — no Qt required."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.search_template_store import SearchTemplate, SearchTemplateStore


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    store = SearchTemplateStore(tmp_path / "nonexistent.toml")
    assert store.templates == []


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "templates.toml"
    store = SearchTemplateStore(path)
    store.save(SearchTemplate(name="py files", pattern="*.py", mode="wildcard", max_results=500))

    store2 = SearchTemplateStore(path)
    assert len(store2.templates) == 1
    t = store2.templates[0]
    assert t.name == "py files"
    assert t.pattern == "*.py"
    assert t.mode == "wildcard"
    assert t.max_results == 500


def test_save_replaces_existing_by_name(tmp_path: Path) -> None:
    path = tmp_path / "templates.toml"
    store = SearchTemplateStore(path)
    store.save(SearchTemplate(name="dup", pattern="*.txt", mode="wildcard"))
    store.save(SearchTemplate(name="dup", pattern="*.md", mode="regex"))

    store2 = SearchTemplateStore(path)
    assert len(store2.templates) == 1
    assert store2.templates[0].pattern == "*.md"
    assert store2.templates[0].mode == "regex"


def test_delete_removes_template(tmp_path: Path) -> None:
    path = tmp_path / "templates.toml"
    store = SearchTemplateStore(path)
    store.save(SearchTemplate(name="gone", pattern="*.log", mode="wildcard"))
    store.delete("gone")

    store2 = SearchTemplateStore(path)
    assert store2.templates == []


def test_toml_format_is_table_array(tmp_path: Path) -> None:
    path = tmp_path / "templates.toml"
    store = SearchTemplateStore(path)
    store.save(SearchTemplate(name="test", pattern="*.rs", mode="content", max_results=200))

    raw = path.read_text()
    assert "[[templates]]" in raw
    assert 'name = "test"' in raw
    assert 'pattern = "*.rs"' in raw
