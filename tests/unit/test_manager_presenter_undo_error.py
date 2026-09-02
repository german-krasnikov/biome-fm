"""C39 — ManagerPresenter undo/redo must surface OSError via EventBus."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from biome_fm.event_bus import EventBus, OperationFinished
from biome_fm.models.vfs import LocalVFS
from biome_fm.presenters.manager_presenter import ManagerPresenter


def _make_presenter():
    bus = EventBus()
    bus.events: list = []
    bus.subscribe(OperationFinished, lambda e: bus.events.append(e))
    left = MagicMock()
    right = MagicMock()
    vfs = LocalVFS()
    mp = ManagerPresenter(left, right, vfs, bus=bus)
    return mp, bus


def test_undo_oserror_publishes_operation_finished():
    mp, bus = _make_presenter()
    with (
        patch.object(mp._history, "undo", side_effect=OSError("disk gone")),
        patch.object(mp, "_refresh_both") as mock_refresh,
    ):
        mp.undo()
        mock_refresh.assert_not_called()

    assert len(bus.events) == 1
    ev = bus.events[0]
    assert isinstance(ev, OperationFinished)
    assert ev.description == "Undo"
    assert ev.success is False
    assert "disk gone" in ev.error


def test_redo_oserror_publishes_operation_finished():
    mp, bus = _make_presenter()
    with (
        patch.object(mp._history, "redo", side_effect=OSError("no space")),
        patch.object(mp, "_refresh_both") as mock_refresh,
    ):
        mp.redo()
        mock_refresh.assert_not_called()

    assert len(bus.events) == 1
    ev = bus.events[0]
    assert isinstance(ev, OperationFinished)
    assert ev.description == "Redo"
    assert ev.success is False
    assert "no space" in ev.error
