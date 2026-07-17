"""#60 — Persistent Marks Across Navigation (LRU 20)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.pane_presenter import PanePresenter


def _item(name: str, is_dir: bool = False) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=is_dir, size=0, modified=0.0)


def _make_presenter(dirs: list[str]) -> tuple[PanePresenter, MagicMock]:
    """Return (presenter, view_mock). VFS listdir returns dirs as FileItems."""
    view = MagicMock()
    view.current_cursor_item.return_value = None
    view.set_items.return_value = None

    vfs = MagicMock()
    # Build per-path item lists
    item_map: dict[Path, list[FileItem]] = {}
    for d in dirs:
        p = Path(d)
        item_map[p] = []
    vfs.listdir.side_effect = lambda path: item_map.get(path, [])

    p = PanePresenter(view=view, vfs=vfs, home=Path(dirs[0]))
    return p, view


def test_marks_saved_on_navigate(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir(); dir_b.mkdir()

    view = MagicMock()
    view.current_cursor_item.return_value = None
    vfs = MagicMock()
    file_a = FileItem(name="x.txt", path=dir_a / "x.txt", is_dir=False, size=0, modified=0.0)
    vfs.listdir.side_effect = lambda p: [file_a] if p == dir_a else []

    presenter = PanePresenter(view=view, vfs=vfs, home=dir_a)
    presenter.navigate_to(dir_a)

    # Mark x.txt
    presenter._marks.add(file_a.path)

    # Navigate away — marks should be saved
    presenter.navigate_to(dir_b)

    assert dir_a in presenter._persistent_marks
    assert file_a.path in presenter._persistent_marks[dir_a]


def test_marks_restored_on_return(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir(); dir_b.mkdir()

    view = MagicMock()
    view.current_cursor_item.return_value = None
    vfs = MagicMock()
    file_a = FileItem(name="x.txt", path=dir_a / "x.txt", is_dir=False, size=0, modified=0.0)
    vfs.listdir.side_effect = lambda p: [file_a] if p == dir_a else []

    presenter = PanePresenter(view=view, vfs=vfs, home=dir_a)
    presenter.navigate_to(dir_a)
    presenter._marks.add(file_a.path)

    presenter.navigate_to(dir_b)   # save marks for dir_a
    presenter.navigate_to(dir_a)   # restore marks for dir_a

    assert file_a.path in presenter._marks


def test_lru_eviction(tmp_path):
    """After visiting 21 unique dirs, the oldest is evicted from _persistent_marks."""
    dirs = [tmp_path / f"d{i}" for i in range(22)]
    for d in dirs:
        d.mkdir()

    view = MagicMock()
    view.current_cursor_item.return_value = None
    vfs = MagicMock()
    # Each dir has one file to mark
    def listdir(p):
        f = FileItem(name="f.txt", path=p / "f.txt", is_dir=False, size=0, modified=0.0)
        return [f]
    vfs.listdir.side_effect = listdir

    presenter = PanePresenter(view=view, vfs=vfs)

    for i, d in enumerate(dirs):
        presenter.navigate_to(d)
        if i < len(dirs) - 1:
            # Mark current file
            f_path = d / "f.txt"
            presenter._marks.add(f_path)

    # dirs[0] should be evicted (21 dirs with marks means 21 entries, max is 20)
    assert len(presenter._persistent_marks) <= 20
    assert dirs[0] not in presenter._persistent_marks
