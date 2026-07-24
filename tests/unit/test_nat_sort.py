"""Natural sort correctness — _sort in PanePresenter must use nat_key."""
from pathlib import Path
from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import _sort


def _f(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(name), is_dir=is_dir, size=0, modified=0.0)


def test_sort_natural_order():
    items = [_f("a10"), _f("a1"), _f("a2")]
    assert [i.name for i in _sort(items)] == ["a1", "a2", "a10"]


def test_sort_file_extensions():
    items = [_f("file10.txt"), _f("file1.txt"), _f("file2.txt")]
    assert [i.name for i in _sort(items)] == ["file1.txt", "file2.txt", "file10.txt"]


def test_sort_dirs_before_files():
    items = [_f("z_file"), _f("a_dir", is_dir=True)]
    assert _sort(items) == [_f("a_dir", is_dir=True), _f("z_file")]
