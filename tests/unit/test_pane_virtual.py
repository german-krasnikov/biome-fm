"""Tests for PanePresenter.navigate_virtual() — virtual item list display."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _make_presenter(cwd: Path | None = None):
    from biome_fm.models.file_item import FileItem
    from biome_fm.presenters.pane_presenter import PanePresenter

    view = MagicMock()
    view.current_cursor_item.return_value = None

    vfs = MagicMock()
    vfs.listdir.return_value = []

    p = PanePresenter(view=view, vfs=vfs)
    if cwd is not None:
        p.navigate_to(cwd)
    return p, view, vfs


def _make_item(name: str, path: str | None = None) -> "FileItem":
    from biome_fm.models.file_item import FileItem

    return FileItem(name=name, path=Path(path or f"/fake/{name}"), is_dir=False, size=0, modified=0.0)


def test_navigate_virtual_sets_items_on_view():
    p, view, _ = _make_presenter(Path("/real"))
    items = [_make_item("a.txt"), _make_item("b.txt")]
    view.reset_mock()

    p.navigate_virtual(items, label="Hits")

    view.set_items.assert_called_once_with(items)
    view.set_path.assert_called_once_with(Path("//Hits"))


def test_navigate_virtual_pushes_cwd_to_back_stack():
    real = Path("/real")
    p, view, _ = _make_presenter(real)

    p.navigate_virtual([_make_item("x")])

    assert real in p._back


def test_navigate_virtual_clears_marks():
    real = Path("/real")
    p, view, _ = _make_presenter(real)
    p._marks = {Path("/real/foo")}

    p.navigate_virtual([_make_item("y")])

    assert p._marks == set()
    view.set_marked.assert_called_with(set())


def test_go_back_from_virtual_restores_real_dir():
    real = Path("/real")
    p, view, vfs = _make_presenter(real)
    vfs.listdir.return_value = []

    p.navigate_virtual([_make_item("z")])
    p.go_back()

    assert p._cwd == real


def test_virtual_activate_override_called_on_open():
    p, view, _ = _make_presenter(Path("/real"))
    item = _make_item("result.txt")
    activated = []

    p.navigate_virtual([item], on_activate=activated.append)
    p.on_item_activated(item)

    assert activated == [item]


def test_is_virtual_false_for_real_dir():
    p, _, _ = _make_presenter(Path("/real"))
    assert not p._is_virtual()


def test_is_virtual_true_after_navigate_virtual():
    p, _, _ = _make_presenter(Path("/real"))
    p.navigate_virtual([_make_item("x")])
    assert p._is_virtual()


def test_go_back_clears_virtual_activate():
    p, view, vfs = _make_presenter(Path("/real"))
    vfs.listdir.return_value = []
    activated = []

    p.navigate_virtual([_make_item("x")], on_activate=activated.append)
    p.go_back()

    # After going back, activating a real dir item should NOT call the old callback
    from biome_fm.models.file_item import FileItem
    real_item = FileItem(name="sub", path=Path("/real/sub"), is_dir=True, size=0, modified=0.0)
    vfs.listdir.return_value = []
    p.on_item_activated(real_item)  # should do navigate_to, not the callback
    assert activated == []
