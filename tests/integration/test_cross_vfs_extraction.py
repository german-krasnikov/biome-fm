"""Integration tests for cross-VFS extraction (archive pane → local pane)."""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs_router import VFSRouter
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


def _make_zip(path: Path, files: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return path


def _item(path: Path, is_dir: bool = False) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=is_dir, size=0, modified=0.0)


@pytest.fixture()
def setup(tmp_path: Path):
    arc = _make_zip(tmp_path / "archive.zip", {
        "file.txt": b"hello from archive",
        "subdir/nested.txt": b"nested content",
    })
    local_dir = tmp_path / "local"
    local_dir.mkdir()

    router = VFSRouter()
    lv, rv = FakePaneView(), FakePaneView()
    left = PanePresenter(lv, router)
    right = PanePresenter(rv, router)
    left.navigate_to(arc)
    right.navigate_to(local_dir)
    manager = ManagerPresenter(left, right, router)
    return manager, arc, local_dir


def test_f5_from_archive_pane_extracts_file(setup, tmp_path: Path) -> None:
    manager, arc, local_dir = setup
    # Simulate: active pane is left (archive), copy file.txt to right (local)
    item = _item(arc / "file.txt")
    manager.copy_selected([item])
    assert (local_dir / "file.txt").read_bytes() == b"hello from archive"


def test_extract_creates_target_dirs(setup, tmp_path: Path) -> None:
    manager, arc, local_dir = setup
    # Copy a dir entry — structure should be preserved under local_dir
    item = _item(arc / "subdir", is_dir=True)
    manager.copy_selected([item])
    assert (local_dir / "subdir" / "nested.txt").read_bytes() == b"nested content"
