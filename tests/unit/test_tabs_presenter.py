"""TDD: TabsPresenter — no Qt."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from biome_fm.models.file_item import FileItem
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.tabs_presenter import TabsPresenter

# ── fakes ────────────────────────────────────────────────────────────────────

class _FakeTabsView:
    def __init__(self) -> None:
        self.tabs: list[str] = []
        self.active: int = 0
        self.titles: dict[int, str] = {}

    def add_tab(self, title: str) -> int:
        self.tabs.append(title)
        return len(self.tabs) - 1

    def remove_tab(self, idx: int) -> None:
        self.tabs.pop(idx)

    def set_active_tab(self, idx: int) -> None:
        self.active = idx

    def set_tab_title(self, idx: int, title: str) -> None:
        self.titles[idx] = title

    def set_tab_tooltip(self, idx: int, tooltip: str) -> None:
        pass


@dataclass
class _FakePaneView:
    items: list = field(default_factory=list)
    path_text: str = ""
    error: str = ""
    status_text: str = ""
    marked_paths: set = field(default_factory=set)

    def set_items(self, items: list) -> None:
        self.items = items

    def set_path(self, path: Path) -> None:
        self.path_text = str(path)

    def show_error(self, msg: str) -> None:
        self.error = msg

    def set_status(self, text: str) -> None:
        self.status_text = text

    def set_marked(self, paths: set) -> None:
        self.marked_paths = paths

    def current_cursor_item(self) -> FileItem | None:
        return None

    def advance_cursor(self) -> None:
        pass

    def retreat_cursor(self) -> None:
        pass

    def set_filter_visible(self, visible: bool) -> None:
        pass

    def set_nav_history(self, paths: list) -> None:
        pass


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    return tmp_path


@pytest.fixture
def vfs() -> LocalVFS:
    return LocalVFS()


def make_presenter(vfs: LocalVFS) -> tuple[TabsPresenter, _FakeTabsView]:
    tv = _FakeTabsView()
    views: list[_FakePaneView] = []

    def view_factory() -> _FakePaneView:
        v = _FakePaneView()
        views.append(v)
        return v

    tp = TabsPresenter(vfs=vfs, tabs_view=tv, view_factory=view_factory)
    return tp, tv


# ── tests ─────────────────────────────────────────────────────────────────────

def test_new_tab_creates_presenter(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    assert tp.tab_count == 1


def test_new_tab_navigates(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    assert tp.current_path == root


def test_two_tabs(root: Path, vfs: LocalVFS) -> None:
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    assert tp.tab_count == 2
    assert tp.active_idx == 1
    assert tv.active == 1


def test_close_tab_single_noop(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    tp.close_tab(0)
    assert tp.tab_count == 1


def test_close_tab_removes(root: Path, vfs: LocalVFS) -> None:
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    tp.close_tab(1)
    assert tp.tab_count == 1
    assert tp.active_idx == 0
    assert tv.active == 0


def test_close_active_adjusts_idx(root: Path, vfs: LocalVFS) -> None:
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    tp.close_tab(0)
    assert tp.tab_count == 1
    assert tp.active_idx == 0
    assert tv.active == 0


def test_switch_tab(root: Path, vfs: LocalVFS) -> None:
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    tp.switch_tab(0)
    assert tp.active_idx == 0
    assert tv.active == 0


def test_switch_tab_invalid(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    tp.switch_tab(99)
    assert tp.active_idx == 0


def test_current_path_delegates(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    assert tp.current_path == root / "dir1"


def test_paths_returns_all(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    assert set(tp.paths()) == {root / "dir1", root / "dir2"}


def test_navigate_updates_tab_title(root: Path, vfs: LocalVFS) -> None:
    tp, tv = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.navigate_to(root / "dir2")
    assert tv.titles[0] == str(root / "dir2")


def test_refresh_delegates(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root)
    # refresh should not raise and current_path stays the same
    tp.refresh()
    assert tp.current_path == root


def test_view_at_returns_correct_view(root: Path, vfs: LocalVFS) -> None:
    tv = _FakeTabsView()
    captured: list[_FakePaneView] = []

    def view_factory() -> _FakePaneView:
        v = _FakePaneView()
        captured.append(v)
        return v

    tp = TabsPresenter(vfs=vfs, tabs_view=tv, view_factory=view_factory)
    tp.new_tab(root / "dir1")
    tp.new_tab(root / "dir2")
    assert tp.view_at(0) is captured[0]
    assert tp.view_at(1) is captured[1]
