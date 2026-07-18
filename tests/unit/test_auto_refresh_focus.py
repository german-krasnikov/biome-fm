"""Unit tests for F246 — Auto-Refresh with focus/unfocus."""
from __future__ import annotations

from unittest.mock import MagicMock, call

from biome_fm.app import _handle_app_state_change
from biome_fm.qt import Qt


def test_pause_on_unfocus() -> None:
    watch_timer = MagicMock()
    refresh_timer = MagicMock()
    drain = MagicMock()

    _handle_app_state_change(
        Qt.ApplicationState.ApplicationInactive,
        watch_timer, refresh_timer, drain,
    )

    watch_timer.stop.assert_called_once()
    refresh_timer.stop.assert_called_once()
    drain.assert_not_called()


def test_resume_on_focus() -> None:
    watch_timer = MagicMock()
    refresh_timer = MagicMock()
    drain = MagicMock()

    _handle_app_state_change(
        Qt.ApplicationState.ApplicationActive,
        watch_timer, refresh_timer, drain,
    )

    watch_timer.start.assert_called_once()
    refresh_timer.start.assert_called_once()
    drain.assert_called_once()
