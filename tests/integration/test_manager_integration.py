"""Integration tests for ManagerPresenter — real LocalVFS + real filesystem."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.commands.base import CommandHistory
from biome_fm.event_bus import EventBus
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter

# ── minimal fake view (no Qt) ─────────────────────────────────────────────────

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


# ── helpers ───────────────────────────────────────────────────────────────────

def _item(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=path.is_dir(), size=0, modified=0.0)


@pytest.fixture()
def setup(tmp_path: Path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()

    vfs = LocalVFS()
    lv, rv = FakePaneView(), FakePaneView()
    lp = PanePresenter(lv, vfs)
    rp = PanePresenter(rv, vfs)
    lp.navigate_to(left_dir)
    rp.navigate_to(right_dir)

    mgr = ManagerPresenter(lp, rp, vfs, history=CommandHistory(), bus=EventBus())
    return mgr, left_dir, right_dir


# ── tests ─────────────────────────────────────────────────────────────────────

def test_copy_between_panes(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "a.txt"
    f.write_text("hello")

    mgr.copy_selected([_item(f)])

    assert (right_dir / "a.txt").exists()
    assert f.exists()  # original intact


def test_move_between_panes(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "b.txt"
    f.write_text("world")

    mgr.move_selected([_item(f)])

    assert (right_dir / "b.txt").exists()
    assert not f.exists()


def test_undo_copy_removes_from_target(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "c.txt"
    f.write_text("copy me")
    mgr.copy_selected([_item(f)])
    assert (right_dir / "c.txt").exists()

    mgr.undo()

    assert not (right_dir / "c.txt").exists()
    assert f.exists()


def test_undo_move_restores_source(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "m.txt"
    f.write_text("move me")
    mgr.move_selected([_item(f)])
    assert not f.exists()

    mgr.undo()

    assert f.exists()
    assert not (right_dir / "m.txt").exists()


def test_redo_after_undo(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "r.txt"
    f.write_text("redo me")
    mgr.copy_selected([_item(f)])
    mgr.undo()
    assert not (right_dir / "r.txt").exists()

    mgr.redo()

    assert (right_dir / "r.txt").exists()


def test_mkdir_creates_directory(setup):
    mgr, left_dir, right_dir = setup

    mgr.mkdir("new_folder")

    assert (left_dir / "new_folder").is_dir()


def test_rename_changes_name(setup):
    mgr, left_dir, right_dir = setup
    f = left_dir / "old.txt"
    f.write_text("data")

    mgr.rename(_item(f), "new.txt")

    assert (left_dir / "new.txt").exists()
    assert not f.exists()


def test_switch_pane_changes_target(setup):
    mgr, left_dir, right_dir = setup
    f = right_dir / "x.txt"
    f.write_text("switch test")

    mgr.switch_active_pane()  # active=right, target=left
    mgr.copy_selected([_item(f)])

    assert (left_dir / "x.txt").exists()
    assert f.exists()  # original in right still there
