"""Unit tests for F278 — File Grouping (_group_key logic, no Qt)."""
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem


def _item(name: str, *, is_dir: bool = False, modified: float = 0.0, size: int = 0) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=is_dir, size=size, modified=modified)


class TestGroupKey:
    def test_group_none_returns_empty(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        item = _item("foo.py")
        assert _group_key(item, GroupByMode.NONE) == ""

    def test_group_by_kind_code(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        for name in ("foo.py", "bar.js", "baz.c", "qux.go", "main.rs"):
            assert _group_key(_item(name), GroupByMode.KIND) == "Code", name

    def test_group_by_kind_docs(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        for name in ("report.pdf", "notes.md", "readme.txt"):
            assert _group_key(_item(name), GroupByMode.KIND) == "Documents", name

    def test_group_by_kind_images(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        for name in ("photo.jpg", "logo.png", "icon.svg"):
            assert _group_key(_item(name), GroupByMode.KIND) == "Images", name

    def test_group_by_kind_folders(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        assert _group_key(_item("mydir", is_dir=True), GroupByMode.KIND) == "Folders"

    def test_group_by_kind_other(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        assert _group_key(_item("mystery.xyz"), GroupByMode.KIND) == "Other"

    def test_group_by_first_letter(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        assert _group_key(_item("Alpha.txt"), GroupByMode.FIRST_LETTER) == "A"
        assert _group_key(_item("beta.py"), GroupByMode.FIRST_LETTER) == "B"
        assert _group_key(_item(".hidden"), GroupByMode.FIRST_LETTER) == "."

    def test_group_by_size_buckets(self):
        from biome_fm.models.directory_model import GroupByMode, _group_key
        assert _group_key(_item("tiny.txt", size=500), GroupByMode.SIZE) == "Tiny (<1 KB)"
        assert _group_key(_item("small.txt", size=50_000), GroupByMode.SIZE) == "Small (<1 MB)"
        assert _group_key(_item("big.bin", size=200_000_000), GroupByMode.SIZE) == "Large (>100 MB)"

    def test_group_by_kind_separates_extensions(self):
        """Grouping by kind puts .py and .txt in different groups."""
        from biome_fm.models.directory_model import GroupByMode, _group_key
        py = _item("foo.py")
        txt = _item("bar.txt")
        assert _group_key(py, GroupByMode.KIND) != _group_key(txt, GroupByMode.KIND)

    def test_group_none_no_separators(self):
        """NONE mode returns empty string for all items."""
        from biome_fm.models.directory_model import GroupByMode, _group_key
        for item in [_item("a.py"), _item("b.txt"), _item("dir", is_dir=True)]:
            assert _group_key(item, GroupByMode.NONE) == ""
