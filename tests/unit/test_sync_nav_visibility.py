"""Unit tests for sync browsing event publishing (no Qt)."""
from __future__ import annotations

from biome_fm.event_bus import EventBus, SyncBrowsingToggled
from biome_fm.presenters.manager_presenter import ManagerPresenter


def _make_manager(bus: EventBus) -> ManagerPresenter:
    from unittest.mock import MagicMock
    return ManagerPresenter(MagicMock(), MagicMock(), MagicMock(), bus=bus)


def test_mirror_state_tracked() -> None:
    mgr = _make_manager(EventBus())
    assert mgr.mirror is False
    mgr.toggle_mirror()
    assert mgr.mirror is True
    mgr.toggle_mirror()
    assert mgr.mirror is False


def test_toggle_mirror_publishes_event() -> None:
    bus = EventBus()
    events: list[SyncBrowsingToggled] = []
    bus.subscribe(SyncBrowsingToggled, events.append)

    mgr = _make_manager(bus)
    mgr.toggle_mirror()
    assert events == [SyncBrowsingToggled(enabled=True)]

    mgr.toggle_mirror()
    assert events == [SyncBrowsingToggled(enabled=True), SyncBrowsingToggled(enabled=False)]
