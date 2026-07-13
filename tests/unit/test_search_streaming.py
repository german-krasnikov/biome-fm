"""Test SearchPresenter streaming callbacks."""
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.search_presenter import SearchPresenter


class FakeVFS:
    def __init__(self, tree: dict[Path, list[FileItem]]):
        self._tree = tree

    def listdir(self, path):
        return self._tree.get(path, [])


def _make_item(name, path, is_dir=False):
    return FileItem(name=name, path=path, is_dir=is_dir, size=0, modified=0.0)


def test_on_match_called_for_each_result():
    root = Path("/root")
    items = [
        _make_item("foo.txt", root / "foo.txt"),
        _make_item("bar.txt", root / "bar.txt"),
        _make_item("baz.py", root / "baz.py"),
    ]
    vfs = FakeVFS({root: items})
    sp = SearchPresenter(vfs, root)
    matches = []
    results = sp.search("*.txt", on_match=matches.append)
    assert len(matches) == 2
    assert len(results) == 2
    assert matches == results


def test_on_match_not_called_when_none():
    root = Path("/root")
    vfs = FakeVFS({root: [_make_item("foo.txt", root / "foo.txt")]})
    sp = SearchPresenter(vfs, root)
    results = sp.search("*.txt")  # no callback
    assert len(results) == 1


def test_on_progress_called_per_directory():
    root = Path("/root")
    sub = root / "sub"
    vfs = FakeVFS({
        root: [_make_item("sub", sub, is_dir=True), _make_item("a.txt", root / "a.txt")],
        sub: [_make_item("b.txt", sub / "b.txt")],
    })
    sp = SearchPresenter(vfs, root)
    dirs = []
    sp.search("*.txt", on_progress=dirs.append)
    assert root in dirs
    assert sub in dirs


def test_on_match_with_cancel():
    root = Path("/root")
    items = [_make_item(f"f{i}.txt", root / f"f{i}.txt") for i in range(10)]
    vfs = FakeVFS({root: items})
    sp = SearchPresenter(vfs, root)
    matches = []

    def _on_match(r):
        matches.append(r)
        if len(matches) >= 3:
            sp.cancel()

    sp.search("*.txt", on_match=_on_match)
    assert len(matches) == 3


def test_on_progress_not_called_when_none():
    root = Path("/root")
    vfs = FakeVFS({root: []})
    sp = SearchPresenter(vfs, root)
    sp.search("*.txt")  # no crash, no callback
