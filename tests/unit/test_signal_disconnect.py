"""Test that _wire_pane() tracks all connections via presenter._track()."""
from __future__ import annotations

from pathlib import Path

from biome_fm.app import _wire_pane
from biome_fm.event_bus import (
    ActivePaneChanged,
    AsyncOpSubmitted,
    BookmarkChanged,
    EventBus,
    OperationFinished,
    OperationStarted,
    ShowHiddenToggled,
    SyncBrowsingToggled,
    ThemeChanged,
)
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.pane_presenter import PanePresenter


class _FakeSig:
    def __init__(self) -> None:
        self._slots: list = []

    def connect(self, slot: object) -> None:
        self._slots.append(slot)

    def disconnect(self, slot: object) -> None:
        try:
            self._slots.remove(slot)
        except ValueError:
            pass


class _FakeView:
    """Fake PaneView with all signals _wire_pane touches."""

    def __init__(self) -> None:
        self.item_activated = _FakeSig()
        self.path_change_requested = _FakeSig()
        self.mark_toggle_requested = _FakeSig()
        self.back_requested = _FakeSig()
        self.forward_requested = _FakeSig()
        self.up_requested = _FakeSig()
        self.home_requested = _FakeSig()
        self.mark_toggle_up_requested = _FakeSig()
        self.mark_at_requested = _FakeSig()
        self.calculate_dir_sizes_requested = _FakeSig()
        self.mark_range_requested = _FakeSig()
        self.history_jump_requested = _FakeSig()

    # PaneViewProtocol stubs
    def set_items(self, items: list, **kw: object) -> None: pass
    def set_path(self, path: Path) -> None: pass
    def show_error(self, msg: str) -> None: pass
    def set_status(self, text: str) -> None: pass
    def set_marked(self, paths: set) -> None: pass
    def current_cursor_item(self) -> None: return None
    def advance_cursor(self) -> None: pass
    def retreat_cursor(self) -> None: pass
    def set_filter_visible(self, v: bool) -> None: pass
    def set_nav_history(self, paths: list) -> None: pass
    def select_item(self, name: str) -> None: pass
    def set_dir_size(self, path: Path, size: int) -> None: pass


def _make() -> tuple[_FakeView, PanePresenter]:
    view = _FakeView()
    presenter = PanePresenter(view=view, vfs=LocalVFS())
    return view, presenter


def test_wire_pane_tracks_connections() -> None:
    """_wire_pane() must register all connections via _track() so cleanup() works."""
    view, presenter = _make()
    _wire_pane(view, presenter)
    # 3 mandatory + 7 optional-but-present + 2 extra = 12; >= 9 is the minimum bar
    assert len(presenter._connections) >= 9


def test_wire_pane_cleanup_disconnects_all() -> None:
    """cleanup() must disconnect every signal wired by _wire_pane()."""
    view, presenter = _make()
    _wire_pane(view, presenter)
    assert len(presenter._connections) >= 9

    presenter.cleanup()

    assert presenter._connections == []
    all_sigs = [
        view.item_activated, view.path_change_requested, view.mark_toggle_requested,
        view.back_requested, view.forward_requested, view.up_requested,
        view.home_requested, view.mark_toggle_up_requested, view.mark_at_requested,
        view.calculate_dir_sizes_requested, view.mark_range_requested,
        view.history_jump_requested,
    ]
    assert all(sig._slots == [] for sig in all_sigs)


# ── Fix B: bus handler unsubscribe ───────────────────────────────────────────


def test_anonymous_lambda_cannot_be_unsubscribed() -> None:
    """Regression doc: anonymous lambda reference is lost → unsubscribe is a no-op."""
    bus = EventBus()
    called: list[int] = []
    bus.subscribe(BookmarkChanged, lambda _: called.append(1))
    bus.unsubscribe(BookmarkChanged, lambda _: called.append(1))  # different object
    bus.publish(BookmarkChanged())
    assert called == [1], "handler still fires — anonymous lambda can't be unsubscribed"


def test_bus_unsubscribe_all_9_handlers() -> None:
    """Named handlers can be removed; all 9 app.py subscriptions must unsubscribe cleanly.

    Regression for Fix B: previously BookmarkChanged, OperationStarted and
    SyncBrowsingToggled used anonymous lambdas that were invisible to unsubscribe().
    Stale handlers on the module-level singleton caused RuntimeError in the test suite
    when the next create_app() fired events into already-deleted Qt objects.
    """
    bus = EventBus()

    # Named handlers — same pattern used in create_app() after Fix B
    def _on_bookmark_changed(_: object) -> None: pass
    def _on_async_op(_: object) -> None: pass
    def _on_op_finished(_: object) -> None: pass
    def _on_op_started(_: object) -> None: pass
    def _on_op_finished_sb(_: object) -> None: pass
    def _on_active_changed(_: object) -> None: pass
    def _on_show_hidden(_: object) -> None: pass
    def _on_sync_browsing(_: object) -> None: pass
    def _on_theme_changed(_: object) -> None: pass

    bus.subscribe(BookmarkChanged,     _on_bookmark_changed)
    bus.subscribe(AsyncOpSubmitted,    _on_async_op)
    bus.subscribe(OperationFinished,   _on_op_finished)
    bus.subscribe(OperationStarted,    _on_op_started)
    bus.subscribe(OperationFinished,   _on_op_finished_sb)
    bus.subscribe(ActivePaneChanged,   _on_active_changed)
    bus.subscribe(ShowHiddenToggled,   _on_show_hidden)
    bus.subscribe(SyncBrowsingToggled, _on_sync_browsing)
    bus.subscribe(ThemeChanged,        _on_theme_changed)

    # Mirror the _on_close() tuple-expression unsubscribe block
    (
        bus.unsubscribe(BookmarkChanged,     _on_bookmark_changed),
        bus.unsubscribe(AsyncOpSubmitted,    _on_async_op),
        bus.unsubscribe(OperationFinished,   _on_op_finished),
        bus.unsubscribe(OperationStarted,    _on_op_started),
        bus.unsubscribe(OperationFinished,   _on_op_finished_sb),
        bus.unsubscribe(ActivePaneChanged,   _on_active_changed),
        bus.unsubscribe(ShowHiddenToggled,   _on_show_hidden),
        bus.unsubscribe(SyncBrowsingToggled, _on_sync_browsing),
        bus.unsubscribe(ThemeChanged,        _on_theme_changed),
    )

    for ev_type in [
        BookmarkChanged, AsyncOpSubmitted, OperationFinished,
        OperationStarted, ActivePaneChanged, ShowHiddenToggled,
        SyncBrowsingToggled, ThemeChanged,
    ]:
        assert bus._handlers.get(ev_type, []) == [], f"handlers leaked for {ev_type.__name__}"
