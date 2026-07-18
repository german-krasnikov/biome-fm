"""Unit tests for PanePresenter.select_by_pattern / deselect_by_pattern."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


def _make_presenter(items: list[FileItem]) -> PanePresenter:
    view = MagicMock()
    vfs = MagicMock()
    vfs.list_dir.return_value = items
    p = PanePresenter(view=view, vfs=vfs, opener=lambda _: None)
    p._items = list(items)
    p._cwd = Path("/tmp")
    return p


def test_select_glob_star_py():
    items = [_item("a.py"), _item("b.txt"), _item("c.py")]
    p = _make_presenter(items)
    p.select_by_pattern("*.py")
    assert p.marks == {Path("/tmp/a.py"), Path("/tmp/c.py")}


def test_deselect_glob():
    items = [_item("a.py"), _item("b.txt"), _item("c.py")]
    p = _make_presenter(items)
    # mark all first
    for i in items:
        p._marks.add(str(i.path))
    p.deselect_by_pattern("*.py")
    assert p.marks == {Path("/tmp/b.txt")}


def test_dotdot_excluded():
    dotdot = FileItem(name="..", path=Path("/tmp"), is_dir=True, size=0, modified=0.0)
    items = [dotdot, _item("a.py")]
    p = _make_presenter(items)
    p.select_by_pattern("*")
    assert Path("/tmp") not in p.marks  # dotdot path must never be marked


def test_pattern_empty_nochange():
    items = [_item("a.py"), _item("b.txt")]
    p = _make_presenter(items)
    p.select_by_pattern("")
    assert len(p._marks) == 0


def test_multiple_patterns_additive():
    items = [_item("a.py"), _item("b.txt"), _item("c.rs")]
    p = _make_presenter(items)
    p.select_by_pattern("*.py")
    p.select_by_pattern("*.txt")
    assert p.marks == {Path("/tmp/a.py"), Path("/tmp/b.txt")}
