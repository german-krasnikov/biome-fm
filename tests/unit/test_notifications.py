"""TDD tests for OS notifications (Feature #76)."""
from __future__ import annotations

from biome_fm.event_bus import OperationFinished


def test_notification_on_operation_finished() -> None:
    from biome_fm.app import _should_show_notification
    ev = OperationFinished("Copy files", success=True)
    assert _should_show_notification(ev, has_active_window=False) is True


def test_no_notification_when_window_focused() -> None:
    from biome_fm.app import _should_show_notification
    ev = OperationFinished("Copy files", success=True)
    assert _should_show_notification(ev, has_active_window=True) is False


def test_no_notification_on_failure() -> None:
    from biome_fm.app import _should_show_notification
    ev = OperationFinished("Copy files", success=False)
    assert _should_show_notification(ev, has_active_window=False) is False
