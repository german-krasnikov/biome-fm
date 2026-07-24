"""Tests for 'info' panel registration in PanelManager (Issue 10)."""
from __future__ import annotations

import pytest

from biome_fm.panel_manager import PanelManager, PanelState


def test_info_initial_state() -> None:
    pm = PanelManager()
    assert pm.state("info") == PanelState.HIDDEN


def test_info_toggle() -> None:
    pm = PanelManager()
    effects = pm.toggle("info")
    kinds = [e.kind for e in effects]
    assert "show_overlay" in kinds
    panels = [e.panel for e in effects if e.kind == "show_overlay"]
    assert "info" in panels


@pytest.mark.parametrize("panel", PanelManager.PANELS)
def test_all_panels_have_state(panel: str) -> None:
    pm = PanelManager()
    # Must not raise KeyError
    state = pm.state(panel)
    assert isinstance(state, PanelState)


def test_save_state_includes_info(tmp_path: pytest.TempPathFactory) -> None:
    """save_state iterates self._panels — 'info' must be in _states to avoid KeyError."""
    # Simulate what PanelCoordinator.save_state does: call state() for each panel name
    pm = PanelManager()
    for name in ("preview", "ai", "search", "terminal", "info"):
        # Must not raise
        _ = pm.state(name).value
