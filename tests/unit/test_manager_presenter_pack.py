"""Tests for ManagerPresenter.pack_to_other_panel (F209)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter


@dataclass
class FakePaneView:
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    status: str = ""
    error: str = ""

    def set_items(self, items: list[FileItem], **kwargs) -> None:
        self.items = items

    def set_path(self, path: Path) -> None:
        self.path = path

    def set_status(self, text: str) -> None:
        self.status = text

    def show_error(self, msg: str) -> None:
        self.error = msg

    def set_marked(self, paths: set) -> None: ...
    def current_cursor_item(self): return None
    def advance_cursor(self) -> None: ...
    def retreat_cursor(self) -> None: ...
    def set_filter_visible(self, visible: bool) -> None: ...
    def set_nav_history(self, paths: list) -> None: ...
    def select_item(self, name: str) -> None: ...


def _make_presenter(left_path: Path, right_path: Path) -> ManagerPresenter:
    vfs = LocalVFS()
    left_view, right_view = FakePaneView(), FakePaneView()
    left = PanePresenter(left_view, vfs)
    right = PanePresenter(right_view, vfs)
    left.navigate_to(left_path)
    right.navigate_to(right_path)
    mgr = ManagerPresenter(left, right, vfs)
    mgr.set_active_pane("left")
    return mgr


def _file_item(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=False, size=5, modified=0.0)


def test_pack_creates_archive_in_opposite_pane(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()

    src_file = src_dir / "myfile.txt"
    src_file.write_text("hello")

    mgr = _make_presenter(src_dir, dst_dir)
    item = _file_item(src_file)

    mgr.pack_to_other_panel([item], fmt="zip")

    archive = dst_dir / "myfile.zip"
    assert archive.exists(), f"Expected {archive} to be created"
    import zipfile
    assert zipfile.is_zipfile(archive)


def test_pack_multiple_uses_dir_name(tmp_path: Path) -> None:
    src_dir = tmp_path / "myproject"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()

    files = []
    for name in ("a.txt", "b.txt"):
        f = src_dir / name
        f.write_text("x")
        files.append(_file_item(f))

    mgr = _make_presenter(src_dir, dst_dir)
    mgr.pack_to_other_panel(files, fmt="zip")

    # multiple items → stem = active pane dir name ("myproject")
    archive = dst_dir / "myproject.zip"
    assert archive.exists()


def test_empty_selection_is_noop(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    dst_dir.mkdir()

    mgr = _make_presenter(src_dir, dst_dir)
    mgr.pack_to_other_panel([], fmt="zip")  # must not raise

    assert list(dst_dir.iterdir()) == []
