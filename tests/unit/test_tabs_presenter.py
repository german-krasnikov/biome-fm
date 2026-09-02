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

    def set_items(self, items: list, **kwargs) -> None:
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

    def select_item(self, name: str) -> None:
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


# ── lock tests ────────────────────────────────────────────────────────────────

def _dir_item(path: Path) -> FileItem:
    return FileItem(name=path.name, path=path, is_dir=True, size=0, modified=0.0)


def test_lock_navigate_opens_new_tab(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.lock_tab(0)
    tp.navigate_to(root / "dir2")
    assert tp.tab_count == 2
    assert tp.current_path == root / "dir2"


def test_lock_on_item_activated_opens_new_tab(root: Path, vfs: LocalVFS) -> None:
    tp, _ = make_presenter(vfs)
    tp.new_tab(root / "dir1")
    tp.lock_tab(0)
    tp.on_item_activated(_dir_item(root / "dir2"))
    assert tp.tab_count == 2


# ── link tests ────────────────────────────────────────────────────────────────

def test_link_navigate_propagates(root: Path, vfs: LocalVFS) -> None:
    a, _ = make_presenter(vfs)
    b, _ = make_presenter(vfs)
    a.new_tab(root / "dir1")
    b.new_tab(root / "dir1")
    a.link_tab(0, b, 0)
    a.navigate_to(root / "dir2")
    assert b._tabs[0].current_path == root / "dir2"


def test_link_no_recursion(root: Path, vfs: LocalVFS) -> None:
    a, _ = make_presenter(vfs)
    b, _ = make_presenter(vfs)
    a.new_tab(root / "dir1")
    b.new_tab(root / "dir1")
    a.link_tab(0, b, 0)
    a.navigate_to(root / "dir2")
    assert a.tab_count == 1
    assert b.tab_count == 1


def test_unlink_stops_propagation(root: Path, vfs: LocalVFS) -> None:
    a, _ = make_presenter(vfs)
    b, _ = make_presenter(vfs)
    a.new_tab(root / "dir1")
    b.new_tab(root / "dir1")
    a.link_tab(0, b, 0)
    a.unlink_tab(0)
    a.navigate_to(root / "dir2")
    assert b._tabs[0].current_path == root / "dir1"


def test_close_tab_shifts_links(root: Path, vfs: LocalVFS) -> None:
    a, _ = make_presenter(vfs)
    b, _ = make_presenter(vfs)
    a.new_tab(root / "dir1")
    a.new_tab(root / "dir2")
    b.new_tab(root / "dir1")
    a.link_tab(1, b, 0)
    a.close_tab(0)
    assert a._links == {0: (b, 0)}
    # Partner back-reference must also be updated — stale index caused IndexError
    assert b._links == {0: (a, 0)}


def test_close_tab_partner_navigate_no_error(root: Path, vfs: LocalVFS) -> None:
    """Regression: b.navigate_to() must not raise IndexError after a.close_tab()."""
    a, _ = make_presenter(vfs)
    b, _ = make_presenter(vfs)
    a.new_tab(root / "dir1")
    a.new_tab(root / "dir2")
    b.new_tab(root / "dir1")
    a.link_tab(1, b, 0)
    a.close_tab(0)
    b.navigate_to(root / "dir2")  # must not raise
    assert a._tabs[0].current_path == root / "dir2"


def test_shutdown_cancels_background_work() -> None:
    """shutdown() calls cleanup() on all active tab presenters."""
    class _MockPresenter:
        cleaned = False
        def cleanup(self) -> None:
            self.cleaned = True

    tv = _FakeTabsView()
    tp = TabsPresenter(vfs=LocalVFS(), tabs_view=tv, view_factory=_FakePaneView)
    m1, m2 = _MockPresenter(), _MockPresenter()
    tp._tabs = [m1, m2]  # type: ignore[list-item]

    tp.shutdown()

    assert m1.cleaned
    assert m2.cleaned


# ── deferred tab safety (C06, C21, C30) ──────────────────────────────────────

def test_paths_with_deferred_tabs(root: Path, vfs: LocalVFS) -> None:
    """paths() must not raise for deferred (not-yet-navigated) tabs."""
    home = root / "dir1"
    other = root / "dir2"
    tp, _ = make_presenter(vfs)
    tp.new_tab(home)
    tp.new_tab(other, deferred=True)
    tp.switch_tab(0)
    # deferred tab should not cause RuntimeError
    result = tp.paths()
    assert result == [home, other]


def test_duplicate_deferred_tab_does_not_raise(root: Path, vfs: LocalVFS) -> None:
    """duplicate_tab() on a deferred tab must not raise RuntimeError."""
    home = root / "dir1"
    other = root / "dir2"
    tp, _ = make_presenter(vfs)
    tp.new_tab(home)
    tp.new_tab(other, deferred=True)
    tp.switch_tab(0)
    tp.duplicate_tab(1)
    assert len(tp.paths()) == 3
