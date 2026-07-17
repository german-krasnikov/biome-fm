"""Unit tests for PanelManager with terminal panel."""
from biome_fm.panel_manager import PanelManager


def test_terminal_in_panels():
    assert "terminal" in PanelManager.PANELS


def test_toggle_terminal():
    pm = PanelManager()
    effects = pm.toggle("terminal")
    assert any(e.kind == "show_overlay" for e in effects)
