"""Per-directory view state — unit tests (no Qt)."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock


PATH_A = Path("/fake/a")
PATH_B = Path("/fake/b")


def _item(path: Path, name: str = "f.txt"):
    from biome_fm.models.file_item import FileItem
    return FileItem(name=name, path=path / name, is_dir=False, size=0, modified=0.0)


def _make_presenter(*, with_state_methods=True):
    """Return (presenter, view, restored_states dict).

    view.get_view_state() returns a fixed ViewState(sort_col=2, ...).
    view.set_view_state() appends calls to restored_states['calls'].
    """
    from biome_fm.models.view_state import ViewState
    from biome_fm.presenters.pane_presenter import PanePresenter

    restored = {"calls": []}

    class StubView:
        def set_items(self, items, **kwargs): pass
        def set_path(self, p): pass
        def show_error(self, m): pass
        def set_status(self, t): pass
        def set_marked(self, p): pass
        def current_cursor_item(self): return None
        def advance_cursor(self): pass
        def retreat_cursor(self): pass
        def set_filter_visible(self, v): pass
        def set_nav_history(self, p): pass
        def select_item(self, name): pass

    if with_state_methods:
        def get_view_state(self):
            return ViewState(sort_col=2, sort_asc=False, filter="txt")
        def set_view_state(self, state):
            restored["calls"].append(state)
        StubView.get_view_state = get_view_state
        StubView.set_view_state = set_view_state

    view = StubView()
    vfs = MagicMock()
    vfs.listdir.side_effect = lambda p: [_item(p)]
    presenter = PanePresenter(view=view, vfs=vfs)
    return presenter, view, restored


# ── 1. ViewState dataclass defaults ──────────────────────────────────────────

def test_view_state_defaults():
    from biome_fm.models.view_state import ViewState
    s = ViewState()
    assert s.sort_col == 0
    assert s.sort_asc is True
    assert s.filter == ""


# ── 2. Navigate A→B saves A's state ──────────────────────────────────────────

def test_navigate_saves_state_for_previous_dir():
    p, view, restored = _make_presenter()
    p.navigate_to(PATH_A)                  # go to A
    p.navigate_to(PATH_B)                  # leave A → should save A's state

    from biome_fm.models.view_state import ViewState
    saved = p._dir_view_state.get(PATH_A)
    assert saved is not None
    assert saved.sort_col == 2
    assert saved.sort_asc is False
    assert saved.filter == "txt"


# ── 3. Navigate back to A restores A's state ─────────────────────────────────

def test_navigate_restores_state_on_return():
    from biome_fm.models.view_state import ViewState
    p, view, restored = _make_presenter()
    p.navigate_to(PATH_A)
    p.navigate_to(PATH_B)   # leave A (saves A's state via get_view_state)
    # Overwrite A's saved state with known values AFTER leaving A
    p._dir_view_state[PATH_A] = ViewState(sort_col=3, sort_asc=True, filter="py")
    p.navigate_to(PATH_A)   # return to A → must restore seeded state

    assert len(restored["calls"]) >= 1
    call = restored["calls"][-1]
    assert call.sort_col == 3
    assert call.filter == "py"


# ── 4. Refresh (same path) does NOT save state ───────────────────────────────

def test_refresh_does_not_save_state():
    p, view, restored = _make_presenter()
    p.navigate_to(PATH_A)
    initial_dict = dict(p._dir_view_state)
    p.refresh()              # same path — must not mutate _dir_view_state[PATH_A]
    assert p._dir_view_state == initial_dict


# ── 5. View without get_view_state doesn't crash ─────────────────────────────

def test_no_crash_when_view_lacks_state_methods():
    p, view, restored = _make_presenter(with_state_methods=False)
    p.navigate_to(PATH_A)
    p.navigate_to(PATH_B)   # no get_view_state → should not raise
    p.navigate_to(PATH_A)   # no set_view_state → should not raise
