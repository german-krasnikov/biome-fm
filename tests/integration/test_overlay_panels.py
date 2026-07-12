"""Integration tests for panel overlay / detach / mutual-exclusion behaviour.

Uses real PreviewPanel and AIChatPanel (not plain QWidget) to catch issues
that only manifest with actual panel implementations.  Coordinator behaviour
with plain widgets is already covered in test_panel_coordinator.py — this
file targets the gaps: AI-specific scenarios, MainWindow signal wiring, and
round-trip state persistence.
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QSplitter, QWidget

from biome_fm.panel_manager import PanelManager, PanelState
from biome_fm.views.ai_chat_panel import AIChatPanel
from biome_fm.views.panel_coordinator import PanelCoordinator
from biome_fm.views.preview_panel import PreviewPanel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def setup(qtbot):
    """Coordinator wired to real panels inside a splitter."""
    splitter = QSplitter(Qt.Orientation.Horizontal)
    left = QWidget()
    right = QWidget()
    preview = PreviewPanel()
    ai = AIChatPanel()
    splitter.addWidget(left)
    splitter.addWidget(right)
    splitter.addWidget(preview)
    splitter.addWidget(ai)
    preview.hide()
    ai.hide()
    splitter.resize(1200, 700)
    splitter.setSizes([600, 600, 0, 0])
    qtbot.addWidget(splitter)
    splitter.show()
    qtbot.waitExposed(splitter)

    mgr = PanelManager()
    coord = PanelCoordinator(
        mgr,
        panels={"preview": preview, "ai": ai},
        left_side=left,
        right_side=right,
        splitter=splitter,
        main_window=splitter,
    )
    return coord, mgr, splitter, left, right, preview, ai


# ---------------------------------------------------------------------------
# AI overlay (standalone)
# ---------------------------------------------------------------------------

def test_toggle_ai_shows_panel_hides_right(setup):
    coord, mgr, _splitter, _left, right, _preview, ai = setup
    coord.toggle("ai")
    assert ai.isVisible()
    assert not right.isVisible()
    assert mgr.state("ai") == PanelState.OVERLAY


def test_toggle_ai_twice_hides_panel_shows_right(setup):
    coord, mgr, _splitter, _left, right, _preview, ai = setup
    coord.toggle("ai")
    coord.toggle("ai")
    assert not ai.isVisible()
    assert right.isVisible()
    assert mgr.state("ai") == PanelState.HIDDEN


def test_ai_overlay_right_pane_size_is_zero(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    coord.toggle("ai")
    idx = splitter.indexOf(right)
    assert splitter.sizes()[idx] == 0


# ---------------------------------------------------------------------------
# Mutual exclusion
# ---------------------------------------------------------------------------

def test_ai_overlay_then_preview_overlay_hides_ai(setup):
    coord, mgr, _splitter, _left, _right, preview, ai = setup
    coord.toggle("ai")
    assert ai.isVisible()
    coord.toggle("preview")
    assert not ai.isVisible()
    assert preview.isVisible()
    assert mgr.state("ai") == PanelState.HIDDEN
    assert mgr.state("preview") == PanelState.OVERLAY


def test_right_pane_stays_hidden_when_overlay_switches(setup):
    """Switching from preview overlay to ai overlay must not show right pane."""
    coord, _mgr, _splitter, _left, right, _preview, _ai = setup
    coord.toggle("preview")
    assert not right.isVisible()
    coord.toggle("ai")
    # right must still be hidden — ai overlay replaced preview
    assert not right.isVisible()


def test_state_changed_emits_for_both_panels_on_mutual_exclusion(setup, qtbot):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    signals: list[tuple[str, str]] = []
    coord.state_changed.connect(lambda name, state: signals.append((name, state)))
    coord.toggle("preview")
    coord.toggle("ai")
    # After second toggle, preview should be hidden and ai overlay
    assert ("preview", "hidden") in signals
    assert ("ai", "overlay") in signals


# ---------------------------------------------------------------------------
# Detach AI panel
# ---------------------------------------------------------------------------

def test_detach_ai_creates_floating_dialog(setup, qtbot):
    coord, mgr, _splitter, _left, right, _preview, _ai = setup
    coord.detach("ai")
    assert mgr.state("ai") == PanelState.FLOATING
    assert "ai" in coord._float
    dlg = coord._float["ai"]
    assert isinstance(dlg, QDialog)
    assert dlg.isVisible()
    assert right.isVisible()  # no overlay → right stays visible
    dlg.close()


def test_float_ai_close_returns_to_hidden(setup, qtbot):
    coord, mgr, _splitter, _left, _right, _preview, ai = setup
    coord.detach("ai")
    dlg = coord._float["ai"]
    dlg.close()
    qtbot.waitUntil(lambda: mgr.state("ai") == PanelState.HIDDEN, timeout=1000)
    assert not ai.isVisible()
    assert "ai" not in coord._float


def test_detach_both_panels_simultaneously(setup, qtbot):
    coord, mgr, _splitter, _left, right, _preview, _ai = setup
    coord.detach("preview")
    coord.detach("ai")
    assert mgr.state("preview") == PanelState.FLOATING
    assert mgr.state("ai") == PanelState.FLOATING
    assert right.isVisible()
    coord._float["preview"].close()
    coord._float["ai"].close()


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def test_save_restore_preview_overlay_round_trip(setup):
    coord, _mgr, splitter, _left, right, preview, ai = setup
    coord.toggle("preview")
    data = coord.save_state()
    assert data["preview"]["state"] == "overlay"
    assert data["ai"]["state"] == "hidden"

    # Fresh coordinator
    mgr2 = PanelManager()
    panels = {"preview": preview, "ai": ai}
    coord2 = PanelCoordinator(mgr2, panels, _left, right, splitter, splitter)
    preview.hide()
    right.show()
    coord2.restore_state(data)
    assert preview.isVisible()
    assert not right.isVisible()
    assert mgr2.state("preview") == PanelState.OVERLAY


def test_save_restore_ai_overlay_round_trip(setup):
    coord, _mgr, splitter, _left, right, preview, ai = setup
    coord.toggle("ai")
    data = coord.save_state()
    assert data["ai"]["state"] == "overlay"

    mgr2 = PanelManager()
    panels = {"preview": preview, "ai": ai}
    coord2 = PanelCoordinator(mgr2, panels, _left, right, splitter, splitter)
    ai.hide()
    right.show()
    coord2.restore_state(data)
    assert ai.isVisible()
    assert mgr2.state("ai") == PanelState.OVERLAY


def test_save_state_both_hidden(setup):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    data = coord.save_state()
    assert data["preview"]["state"] == "hidden"
    assert data["ai"]["state"] == "hidden"
    assert data["preview"]["float_geometry"] == ""
    assert data["ai"]["float_geometry"] == ""


# ---------------------------------------------------------------------------
# Splitter sizes
# ---------------------------------------------------------------------------

def test_preview_overlay_right_pane_size_is_zero(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    coord.toggle("preview")
    idx = splitter.indexOf(right)
    assert splitter.sizes()[idx] == 0


def test_overlay_panel_gets_nonzero_width(setup):
    coord, _mgr, splitter, _left, _right, preview, _ai = setup
    coord.toggle("preview")
    pi = splitter.indexOf(preview)
    assert splitter.sizes()[pi] > 0


def test_ai_overlay_panel_gets_nonzero_width(setup):
    coord, _mgr, splitter, _left, _right, _preview, ai = setup
    coord.toggle("ai")
    pi = splitter.indexOf(ai)
    assert splitter.sizes()[pi] > 0


def test_saved_sizes_restored_after_toggle_off(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    sizes_before = splitter.sizes()[splitter.indexOf(right)]
    coord.toggle("preview")
    coord.toggle("preview")
    sizes_after = splitter.sizes()[splitter.indexOf(right)]
    assert abs(sizes_after - sizes_before) < 10


# ---------------------------------------------------------------------------
# Size transfer (right pane width goes to overlay panel)
# ---------------------------------------------------------------------------

def test_overlay_panel_gets_right_pane_original_width(setup):
    """Panel must get exactly the width the right pane had."""
    coord, _mgr, splitter, _left, right, preview, _ai = setup
    expected = splitter.sizes()[splitter.indexOf(right)]
    coord.toggle("preview")
    assert splitter.sizes()[splitter.indexOf(preview)] == expected


def test_ai_overlay_gets_right_pane_original_width(setup):
    coord, _mgr, splitter, _left, right, _preview, ai = setup
    expected = splitter.sizes()[splitter.indexOf(right)]
    coord.toggle("ai")
    assert splitter.sizes()[splitter.indexOf(ai)] == expected


def test_total_splitter_width_conserved_on_overlay(setup):
    coord, _mgr, splitter, _left, _right, _preview, _ai = setup
    total_before = sum(splitter.sizes())
    coord.toggle("preview")
    assert abs(sum(splitter.sizes()) - total_before) < 5


def test_left_pane_width_unchanged_on_overlay(setup):
    coord, _mgr, splitter, left, _right, _preview, _ai = setup
    left_before = splitter.sizes()[splitter.indexOf(left)]
    coord.toggle("preview")
    assert abs(splitter.sizes()[splitter.indexOf(left)] - left_before) < 5


# ---------------------------------------------------------------------------
# Size restore
# ---------------------------------------------------------------------------

def test_toggle_off_right_pane_exact_width(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    ri = splitter.indexOf(right)
    original = splitter.sizes()[ri]
    coord.toggle("preview")
    coord.toggle("preview")
    assert splitter.sizes()[ri] == original


def test_saved_sizes_cleared_after_toggle_off(setup):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    coord.toggle("preview")
    coord.toggle("preview")
    assert coord._saved_sizes is None


# ---------------------------------------------------------------------------
# Mutual exclusion sizes
# ---------------------------------------------------------------------------

def test_switch_preview_to_ai_ai_gets_original_right_width(setup):
    coord, _mgr, splitter, _left, right, _preview, ai = setup
    original_right = splitter.sizes()[splitter.indexOf(right)]
    coord.toggle("preview")
    coord.toggle("ai")
    assert splitter.sizes()[splitter.indexOf(ai)] == original_right


def test_switch_overlay_saved_sizes_unchanged(setup):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    coord.toggle("preview")
    saved_after_first = dict(coord._saved_sizes)
    coord.toggle("ai")
    assert coord._saved_sizes == saved_after_first


def test_toggle_off_after_mutual_exclusion_restores_original(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    ri = splitter.indexOf(right)
    original = splitter.sizes()[ri]
    coord.toggle("preview")
    coord.toggle("ai")
    coord.toggle("ai")
    assert splitter.sizes()[ri] == original


# ---------------------------------------------------------------------------
# Session restore
# ---------------------------------------------------------------------------

def test_restore_overlay_after_sizes_set_gives_nonzero_width(setup):
    coord, _mgr, splitter, _left, right, preview, ai = setup
    mgr2 = PanelManager()
    panels = {"preview": preview, "ai": ai}
    coord2 = PanelCoordinator(mgr2, panels, _left, right, splitter, splitter)
    splitter.setSizes([600, 600, 0, 0])
    preview.hide()
    right.show()
    coord2.restore_state({
        "preview": {"state": "overlay", "float_geometry": ""},
        "ai": {"state": "hidden", "float_geometry": ""},
    })
    assert splitter.sizes()[splitter.indexOf(preview)] > 0
    assert not right.isVisible()
    del coord  # silence unused var


# ---------------------------------------------------------------------------
# Detach / reattach
# ---------------------------------------------------------------------------

def test_detach_from_overlay_restores_right_to_original_width(setup):
    coord, _mgr, splitter, _left, right, _preview, _ai = setup
    ri = splitter.indexOf(right)
    original = splitter.sizes()[ri]
    coord.toggle("preview")
    coord.detach("preview")
    assert right.isVisible()
    assert abs(splitter.sizes()[ri] - original) < 10


def test_reattach_gives_panel_correct_width(setup):
    coord, _mgr, splitter, _left, right, preview, _ai = setup
    original_right = splitter.sizes()[splitter.indexOf(right)]
    coord.toggle("preview")
    coord.detach("preview")
    coord.reattach("preview")
    assert abs(splitter.sizes()[splitter.indexOf(preview)] - original_right) < 10
    assert not right.isVisible()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_rapid_toggle_preserves_original_sizes(setup):
    coord, _mgr, splitter, _left, _right, _preview, _ai = setup
    original = splitter.sizes()
    for _ in range(4):
        coord.toggle("preview")
        coord.toggle("preview")
    assert splitter.sizes() == original


def test_toggle_floating_panel_focuses_not_changes_size(setup, qtbot):
    coord, mgr, splitter, _left, _right, _preview, _ai = setup
    coord.detach("preview")
    sizes_after_detach = splitter.sizes()
    coord.toggle("preview")  # FLOATING → focus_floating, no size change
    assert mgr.state("preview") == PanelState.FLOATING
    assert splitter.sizes() == sizes_after_detach
    coord._float["preview"].close()


# ---------------------------------------------------------------------------
# Opposite-pane overlay (active=right → overlay on left)
# ---------------------------------------------------------------------------

def test_left_overlay_hides_left_shows_preview(setup):
    coord, _mgr, _splitter, left, right, preview, _ai = setup
    coord.toggle("preview", "right")  # active=right → overlay on left
    assert preview.isVisible()
    assert not left.isVisible()
    assert right.isVisible()


def test_left_overlay_preview_at_index_zero(setup):
    coord, _mgr, splitter, _left, _right, preview, _ai = setup
    coord.toggle("preview", "right")
    assert splitter.indexOf(preview) == 0


def test_left_overlay_panel_gets_left_pane_width(setup):
    coord, _mgr, splitter, left, _right, preview, _ai = setup
    expected = splitter.sizes()[splitter.indexOf(left)]
    coord.toggle("preview", "right")
    assert splitter.sizes()[splitter.indexOf(preview)] == expected


def test_left_overlay_toggle_off_restores_left(setup):
    coord, _mgr, splitter, left, _right, _preview, _ai = setup
    li = splitter.indexOf(left)
    original = splitter.sizes()[li]
    coord.toggle("preview", "right")
    coord.toggle("preview", "right")
    assert left.isVisible()
    assert abs(splitter.sizes()[splitter.indexOf(left)] - original) < 10


def test_left_overlay_ai(setup):
    coord, _mgr, _splitter, left, right, _preview, ai = setup
    coord.toggle("ai", "right")
    assert ai.isVisible()
    assert not left.isVisible()
    assert right.isVisible()


def test_switch_active_pane_mid_overlay_restores_correct_side(setup):
    """Open overlay while left active (hides right), then close while right active."""
    coord, _mgr, _splitter, _left, right, _preview, _ai = setup
    coord.toggle("preview", "left")  # active=left → overlay on right, hides right
    assert not right.isVisible()
    coord.toggle("preview", "right")  # toggle off — should restore RIGHT (the hidden one)
    assert right.isVisible()


def test_left_overlay_mutual_exclusion(setup):
    coord, _mgr, _splitter, left, right, preview, ai = setup
    coord.toggle("preview", "right")  # preview replaces left
    assert not left.isVisible()
    coord.toggle("ai", "right")  # ai replaces preview on left
    assert not preview.isVisible()
    assert ai.isVisible()
    assert not left.isVisible()
    assert right.isVisible()


def test_save_restore_left_overlay_round_trip(setup):
    coord, _mgr, splitter, _left, right, preview, ai = setup
    coord.toggle("preview", "right")  # left overlay
    data = coord.save_state()
    assert data["preview"]["state"] == "overlay"
    assert data["preview"]["overlay_side"] == "left"

    mgr2 = PanelManager()
    panels = {"preview": preview, "ai": ai}
    coord2 = PanelCoordinator(mgr2, panels, _left, right, splitter, splitter)
    preview.hide()
    _left.show()
    coord2.restore_state(data)
    assert preview.isVisible()
    assert not _left.isVisible()
    assert splitter.indexOf(preview) == 0
