"""Unit tests for case-sensitive flag in RenamePresenter (F208)."""
from __future__ import annotations

import re
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.rename_presenter import RenamePresenter


def _item(name: str) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=False, size=0, modified=0.0)


def test_case_sensitive_replace():
    p = RenamePresenter([_item("Foo.txt"), _item("foo.txt")])
    results = p.apply_regex("foo", "bar", flags=0)  # case-sensitive
    assert results[0].new_name == "Foo.txt"  # Foo doesn't match lowercase 'foo'
    assert results[1].new_name == "bar.txt"


def test_case_insensitive_replace():
    p = RenamePresenter([_item("Foo.txt"), _item("foo.txt")])
    results = p.apply_regex("foo", "bar", flags=re.IGNORECASE)
    assert results[0].new_name == "bar.txt"
    assert results[1].new_name == "bar.txt"
