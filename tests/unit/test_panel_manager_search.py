"""PanelManager — search panel integration."""
from biome_fm.panel_manager import PanelManager, PanelState


def test_search_in_panels():
    assert "search" in PanelManager.PANELS


def test_search_starts_hidden():
    mgr = PanelManager()
    assert mgr.state("search") == PanelState.HIDDEN


def test_toggle_search_shows_overlay():
    mgr = PanelManager()
    effects = mgr.toggle("search")
    assert mgr.state("search") == PanelState.OVERLAY
    assert "show_overlay" in [e.kind for e in effects]


def test_search_hides_preview_overlay():
    mgr = PanelManager()
    mgr.toggle("preview")
    effects = mgr.toggle("search")
    assert mgr.state("preview") == PanelState.HIDDEN
    assert mgr.state("search") == PanelState.OVERLAY
    assert any(e.kind == "hide" and e.panel == "preview" for e in effects)


def test_search_hides_ai_overlay():
    mgr = PanelManager()
    mgr.toggle("ai")
    effects = mgr.toggle("search")
    assert mgr.state("ai") == PanelState.HIDDEN
    assert mgr.state("search") == PanelState.OVERLAY


def test_only_one_overlay_at_a_time():
    mgr = PanelManager()
    mgr.toggle("preview")
    mgr.toggle("search")
    overlay_count = sum(1 for p in PanelManager.PANELS if mgr.state(p) == PanelState.OVERLAY)
    assert overlay_count == 1


def test_toggle_search_twice_hides():
    mgr = PanelManager()
    mgr.toggle("search")
    effects = mgr.toggle("search")
    assert mgr.state("search") == PanelState.HIDDEN
    assert any(e.kind == "hide" and e.panel == "search" for e in effects)


def test_search_detach_float():
    mgr = PanelManager()
    mgr.toggle("search")
    effects = mgr.detach("search")
    assert mgr.state("search") == PanelState.FLOATING
    assert any(e.kind == "show_floating" and e.panel == "search" for e in effects)


def test_existing_preview_ai_still_work():
    """Regression: existing preview/ai behavior unchanged."""
    mgr = PanelManager()
    mgr.toggle("preview")
    assert mgr.state("preview") == PanelState.OVERLAY
    effects = mgr.toggle("ai")
    assert mgr.state("preview") == PanelState.HIDDEN
    assert mgr.state("ai") == PanelState.OVERLAY
