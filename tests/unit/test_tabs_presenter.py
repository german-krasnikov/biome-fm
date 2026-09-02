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


# ── close_tab re-entrancy (C32) ───────────────────────────────────────────────

def test_close_tab_loads_pending_neighbour(root: Path, vfs: LocalVFS) -> None:
    """close_tab(active) must eagerly navigate the new active tab if it was deferred."""
    a, b, c = root / "dir1", root / "dir2", root
    tp, _ = make_presenter(vfs)
    tp.new_tab(a, deferred=True)
    tp.new_tab(b, deferred=True)
    tp.new_tab(c, deferred=True)
    tp.switch_tab(1)          # navigates b eagerly; _pending still has {0:a, 2:c}
    tp.close_tab(1)           # close b; new active is index 1 → c (still deferred)
    result = tp.paths()
    assert len(result) == 2
    assert set(result) == {a, c}
    # The newly active tab must have been eagerly navigated (not still deferred)
    assert tp._tabs[tp.active_idx]._cwd is not None


def test_close_tab_shift_happens_before_view_remove(root: Path, vfs: LocalVFS) -> None:
    """_pending must be shifted before remove_tab() fires (re-entrancy guard)."""
    a, b = root / "dir1", root / "dir2"
    pending_snapshot: dict[int, Path] = {}

    class _CapturingTabsView(_FakeTabsView):
        def remove_tab(self, idx: int) -> None:
            # Capture _presenter._pending at the moment Qt would fire currentChanged
            nonlocal pending_snapshot
            pending_snapshot = dict(tp._pending)
            super().remove_tab(idx)

    tv = _CapturingTabsView()
    views: list[_FakePaneView] = []

    def view_factory() -> _FakePaneView:
        v = _FakePaneView()
        views.append(v)
        return v

    tp = TabsPresenter(vfs=vfs, tabs_view=tv, view_factory=view_factory)
    tp.new_tab(a)              # tab 0, navigated
    tp.new_tab(b, deferred=True)  # tab 1, pending at key 1
    tp.close_tab(0)            # close tab 0; tab 1 → index 0

    # At remove_tab call time, _pending must already have key 0 (not 1)
    assert 0 in pending_snapshot, f"_pending was not shifted before remove_tab: {pending_snapshot}"
    assert 1 not in pending_snapshot


# ── on_tab_created callback (C07) ─────────────────────────────────────────────

def test_on_tab_created_called_for_every_new_tab(root: Path, vfs: LocalVFS) -> None:
    """on_tab_created fires for every new_tab() call, including locked-redirect and deferred."""
    home = root / "dir1"
    other = root / "dir2"
    third = root
    tp, _ = make_presenter(vfs)

    created: list[tuple] = []
    tp.on_tab_created = lambda v, p: created.append((v, p))

    tp.new_tab(home)             # idx 0 — fires callback
    tp.new_tab(other)            # idx 1 — fires callback
    tp.lock_tab(1)               # lock active tab
    tp.navigate_to(third)        # locked redirect → new_tab(third) — fires callback

    assert len(created) == 3
    for i in range(3):
        v, p = created[i]
        assert v is tp.view_at(i)
        assert p is tp.presenter_at(i)

    # deferred new_tab also fires the callback
    tp2, _ = make_presenter(vfs)
    deferred_created: list[tuple] = []
    tp2.on_tab_created = lambda v, p: deferred_created.append((v, p))
    tp2.new_tab(home, deferred=True)
    assert len(deferred_created) == 1
    assert deferred_created[0][0] is tp2.view_at(0)
    assert deferred_created[0][1] is tp2.presenter_at(0)


# ── replace_all (C31/C46) ─────────────────────────────────────────────────────

def test_replace_all_replaces_existing_tabs(tmp_path: Path, vfs: LocalVFS) -> None:
    """replace_all([a,b,c], 1) replaces 2 boot tabs with 3 new deferred tabs."""
    a, b, c, home = (tmp_path / x for x in ("a", "b", "c", "home"))
    for d in (a, b, c, home):
        d.mkdir()

    tp, _ = make_presenter(vfs)
    tp.new_tab(home)
    tp.new_tab(home)
    tp.lock_tab(0)

    created: list = []
    tp.on_tab_created = lambda v, p: created.append(p)

    tp.replace_all([a, b, c], 1)

    assert tp.paths() == [a, b, c]
    assert tp.active_idx == 1
    assert tp.presenter_at(1).current_path == b
    assert 0 in tp._pending
    assert 2 in tp._pending
    assert not tp.is_locked(0)
    assert created == [tp.presenter_at(0), tp.presenter_at(1), tp.presenter_at(2)]


def test_replace_all_on_empty_presenter_matches_boot(tmp_path: Path, vfs: LocalVFS) -> None:
    """replace_all on fresh presenter: like _restore with no prior tabs."""
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()

    tp, _ = make_presenter(vfs)
    tp.replace_all([a, b], 0)

    assert tp.paths() == [a, b]
    assert tp.active_idx == 0
    assert 0 not in tp._pending   # active tab was loaded by switch_tab
    assert 1 in tp._pending


def test_replace_all_with_no_paths_keeps_existing_tabs(tmp_path: Path, vfs: LocalVFS) -> None:
    """replace_all([], 0) is a no-op."""
    d1 = tmp_path / "d1"
    d2 = tmp_path / "d2"
    d1.mkdir()
    d2.mkdir()

    tp, _ = make_presenter(vfs)
    tp.new_tab(d1)
    tp.new_tab(d2)
    original_paths = tp.paths()

    tp.replace_all([], 0)

    assert tp.tab_count == 2
    assert tp.paths() == original_paths
