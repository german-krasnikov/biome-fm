"""Unit tests for ManagerPresenter — pure Python, no Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.event_bus import (
    ActivePaneChanged,
    EventBus,
    OperationFinished,
    OperationStarted,
)
from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.manager_presenter import ManagerPresenter
from biome_fm.presenters.pane_presenter import PanePresenter

# ── fakes ─────────────────────────────────────────────────────────────────────

@dataclass
class FakePaneView:
    items: list[FileItem] = field(default_factory=list)
    path: Path | None = None
    status: str = ""
    error: str = ""
    set_items_calls: int = 0

    def set_items(self, items: list[FileItem]) -> None:
        self.items = items
        self.set_items_calls += 1

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


class SpyVFS:
    """Delegates to LocalVFS and records calls."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self._local = LocalVFS()

    def listdir(self, path: Path) -> list[FileItem]:
        return self._local.listdir(path)

    def stat(self, path: Path) -> FileItem:
        return self._local.stat(path)

    def copy(self, src: Path, dst: Path) -> None:
        self.calls.append(("copy", src, dst))
        self._local.copy(src, dst)

    def move(self, src: Path, dst: Path) -> None:
        self.calls.append(("move", src, dst))
        self._local.move(src, dst)

    def delete(self, path: Path) -> None:
        self.calls.append(("delete", path))
        self._local.delete(path)

    def mkdir(self, path: Path) -> None:
        self.calls.append(("mkdir", path))
        self._local.mkdir(path)

    def exists(self, path: Path) -> bool:
        return self._local.exists(path)


# ── fixtures ───────────────────────────────────────────────────────────────────

def _item(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=path.is_dir(), size=0, modified=0.0)


@pytest.fixture()
def setup(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()

    vfs = SpyVFS()
    bus = EventBus()

    lv, rv = FakePaneView(), FakePaneView()
    lp = PanePresenter(lv, vfs)
    rp = PanePresenter(rv, vfs)
    lp.navigate_to(left_dir)
    rp.navigate_to(right_dir)

    mgr = ManagerPresenter(lp, rp, vfs, bus=bus)
    return mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir


# ── tests ──────────────────────────────────────────────────────────────────────

def test_active_pane_defaults_to_left(setup):
    mgr, *_ = setup
    assert mgr.active_pane_id == "left"


def test_switch_active_pane_toggles(setup):
    mgr, *_ = setup
    mgr.switch_active_pane()
    assert mgr.active_pane_id == "right"
    mgr.switch_active_pane()
    assert mgr.active_pane_id == "left"


def test_set_active_pane_same_is_noop(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    received = []
    bus.subscribe(ActivePaneChanged, received.append)
    mgr.set_active_pane("left")  # already left
    assert received == []


def test_copy_selected_to_target_pane(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "a.txt"
    f.write_text("hello")
    mgr.copy_selected([_item(f)])
    assert (right_dir / "a.txt").exists()
    assert (left_dir / "a.txt").exists()  # original intact


def test_copy_empty_list_is_noop(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    mgr.copy_selected([])
    assert [c for c in vfs.calls if c[0] == "copy"] == []


def test_move_selected_to_target_pane(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "b.txt"
    f.write_text("world")
    mgr.move_selected([_item(f)])
    assert (right_dir / "b.txt").exists()
    assert not (left_dir / "b.txt").exists()


def test_delete_selected_calls_vfs(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "del.txt"
    f.write_text("x")
    mgr.delete_selected([_item(f)])
    assert not f.exists()
    assert any(c[0] == "delete" for c in vfs.calls)


def test_mkdir_in_active_pane(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    mgr.mkdir("new_folder")
    assert (left_dir / "new_folder").is_dir()


def test_rename_in_place(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "old.txt"
    f.write_text("data")
    mgr.rename(_item(f), "new.txt")
    assert (left_dir / "new.txt").exists()
    assert not f.exists()


def test_undo_after_copy_removes_dst(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "c.txt"
    f.write_text("copy me")
    mgr.copy_selected([_item(f)])
    assert (right_dir / "c.txt").exists()
    mgr.undo()
    assert not (right_dir / "c.txt").exists()
    assert (left_dir / "c.txt").exists()  # original untouched


def test_undo_after_move_restores_src(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "m.txt"
    f.write_text("move me")
    mgr.move_selected([_item(f)])
    assert not f.exists()
    mgr.undo()
    assert f.exists()
    assert not (right_dir / "m.txt").exists()


def test_redo_after_undo_reapplies(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "r.txt"
    f.write_text("redo me")
    mgr.copy_selected([_item(f)])
    mgr.undo()
    assert not (right_dir / "r.txt").exists()
    mgr.redo()
    assert (right_dir / "r.txt").exists()


def test_delete_not_in_undo_stack(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    f = left_dir / "gone.txt"
    f.write_text("bye")
    mgr.delete_selected([_item(f)])
    assert not mgr.can_undo


def test_operation_refreshes_both_panes(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    calls_before_l = lv.set_items_calls
    calls_before_r = rv.set_items_calls
    f = left_dir / "refresh.txt"
    f.write_text("x")
    mgr.copy_selected([_item(f)])
    assert lv.set_items_calls == calls_before_l + 1
    assert rv.set_items_calls == calls_before_r + 1


def test_bus_receives_operation_started(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    received: list[OperationStarted] = []
    bus.subscribe(OperationStarted, received.append)
    f = left_dir / "ev.txt"
    f.write_text("x")
    mgr.copy_selected([_item(f)])
    assert len(received) == 1
    assert received[0].description == "Copy"


def test_bus_receives_operation_finished(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    received: list[OperationFinished] = []
    bus.subscribe(OperationFinished, received.append)
    f = left_dir / "fin.txt"
    f.write_text("x")
    mgr.copy_selected([_item(f)])
    assert len(received) == 1
    assert received[0].success is True
    assert received[0].description == "Copy"


def test_bus_receives_active_pane_changed(setup):
    mgr, lp, rp, lv, rv, vfs, bus, left_dir, right_dir = setup
    received: list[ActivePaneChanged] = []
    bus.subscribe(ActivePaneChanged, received.append)
    mgr.switch_active_pane()
    assert len(received) == 1
    assert received[0].pane_id == "right"


def test_drop_files_copy(setup):
    mgr, _, _, _, _, _, _, left_dir, right_dir = setup
    f = left_dir / "drop.txt"
    f.write_text("drop")
    mgr.drop_files([f], "right", move=False)
    assert (right_dir / "drop.txt").exists()
    assert f.exists()  # original intact


def test_drop_files_move(setup):
    mgr, _, _, _, _, _, _, left_dir, right_dir = setup
    f = left_dir / "mover.txt"
    f.write_text("move")
    mgr.drop_files([f], "right", move=True)
    assert (right_dir / "mover.txt").exists()
    assert not f.exists()


def test_drop_files_same_dir_noop(setup):
    mgr, _, _, _, _, vfs, _, left_dir, _ = setup
    f = left_dir / "same.txt"
    f.write_text("same")
    before = list(vfs.calls)
    mgr.drop_files([f], "left", move=False)  # dst == f.parent
    assert vfs.calls == before  # no copy/move calls


def test_drop_files_empty_list(setup):
    mgr, _, _, _, _, vfs, _, _, _ = setup
    before = list(vfs.calls)
    mgr.drop_files([], "right", move=False)
    assert vfs.calls == before


def test_no_bus_does_not_crash(tmp_path):
    left_dir = tmp_path / "left"
    right_dir = tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    vfs = SpyVFS()
    lv, rv = FakePaneView(), FakePaneView()
    lp = PanePresenter(lv, vfs)
    rp = PanePresenter(rv, vfs)
    lp.navigate_to(left_dir)
    rp.navigate_to(right_dir)
    mgr = ManagerPresenter(lp, rp, vfs)  # no bus
    mgr.switch_active_pane()  # active=right now; would publish event — should not crash
    f = right_dir / "x.txt"
    f.write_text("x")
    mgr.copy_selected([_item(f)])  # copies right→left; would publish started/finished — no crash
    assert (left_dir / "x.txt").exists()
