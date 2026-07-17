"""TDD: Deferred tab loading on startup."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock


def _make_tabs(vfs=None):
    from biome_fm.presenters.tabs_presenter import TabsPresenter

    vfs = vfs or MagicMock()
    tabs_view = MagicMock()
    tabs_view.add_tab.side_effect = list(range(10))  # 0, 1, 2, ...
    view_factory = MagicMock(return_value=MagicMock())
    return TabsPresenter(vfs, tabs_view, view_factory), vfs


def test_inactive_tab_not_loaded() -> None:
    """Creating a tab with deferred=True must NOT call vfs.listdir."""
    tabs, vfs = _make_tabs()
    vfs.listdir.return_value = []
    tabs.new_tab(Path("/tmp/foo"), deferred=True)
    vfs.listdir.assert_not_called()


def test_normal_tab_loads_immediately() -> None:
    """Default (deferred=False) must call vfs.listdir immediately."""
    tabs, vfs = _make_tabs()
    vfs.listdir.return_value = []
    tabs.new_tab(Path("/tmp/foo"))
    vfs.listdir.assert_called_once()


def test_tab_loads_on_switch() -> None:
    """Switching to a deferred tab triggers navigate_to."""
    tabs, vfs = _make_tabs()
    vfs.listdir.return_value = []

    tabs.new_tab(Path("/tmp/alpha"), deferred=True)
    tabs.new_tab(Path("/tmp/beta"), deferred=True)

    vfs.listdir.assert_not_called()

    # switch to tab 0 — should load /tmp/alpha
    tabs.switch_tab(0)
    assert vfs.listdir.call_count == 1
    called_path = vfs.listdir.call_args[0][0]
    assert called_path == Path("/tmp/alpha")


def test_switch_non_deferred_tab_does_not_double_load() -> None:
    """Switching to an already-loaded tab must not reload."""
    tabs, vfs = _make_tabs()
    vfs.listdir.return_value = []
    tabs.new_tab(Path("/tmp/foo"))  # loaded immediately
    vfs.listdir.reset_mock()
    tabs.switch_tab(0)
    vfs.listdir.assert_not_called()
