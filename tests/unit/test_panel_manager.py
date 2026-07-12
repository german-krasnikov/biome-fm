"""Unit tests for PanelManager — pure Python state machine, no Qt."""
from biome_fm.panel_manager import Effect, PanelManager, PanelState


def effects_of(effects: list[Effect], kind: str) -> list[Effect]:
    return [e for e in effects if e.kind == kind]


def one(effects: list[Effect], kind: str, panel: str = "") -> Effect:
    matches = [e for e in effects if e.kind == kind and (not panel or e.panel == panel)]
    assert len(matches) == 1, f"Expected 1 effect {kind!r}/{panel!r}, got {matches}"
    return matches[0]


# ── 1. Initial state ────────────────────────────────────────────────────────
def test_initial_state():
    pm = PanelManager()
    assert pm.state("preview") == PanelState.HIDDEN
    assert pm.state("ai") == PanelState.HIDDEN


# ── 2. toggle hidden → OVERLAY + hide right ──────────────────────────────────
def test_toggle_hidden_becomes_overlay():
    pm = PanelManager()
    fx = pm.toggle("preview")
    assert pm.state("preview") == PanelState.OVERLAY
    one(fx, "show_overlay", "preview")
    right = one(fx, "set_opposite_visible")
    assert right.value is False


# ── 3. toggle OVERLAY → HIDDEN + show right ──────────────────────────────────
def test_toggle_overlay_becomes_hidden():
    pm = PanelManager()
    pm.toggle("preview")
    fx = pm.toggle("preview")
    assert pm.state("preview") == PanelState.HIDDEN
    one(fx, "hide", "preview")
    right = one(fx, "set_opposite_visible")
    assert right.value is True


# ── 4. toggle FLOATING → focus_floating, no state change ────────────────────
def test_toggle_floating_focuses():
    pm = PanelManager()
    pm.detach("preview")  # hidden → floating
    fx = pm.toggle("preview")
    assert pm.state("preview") == PanelState.FLOATING
    one(fx, "focus_floating", "preview")
    assert len(fx) == 1  # nothing else


# ── 5. Mutual exclusion: preview OVERLAY + toggle(ai) ────────────────────────
def test_mutual_exclusion_overlay():
    pm = PanelManager()
    pm.toggle("preview")  # preview → OVERLAY
    fx = pm.toggle("ai")
    assert pm.state("ai") == PanelState.OVERLAY
    assert pm.state("preview") == PanelState.HIDDEN
    one(fx, "hide", "preview")
    one(fx, "show_overlay", "ai")
    right = one(fx, "set_opposite_visible")
    assert right.value is False


# ── 6. detach(hidden) → FLOATING, right stays visible ───────────────────────
def test_detach_from_hidden():
    pm = PanelManager()
    fx = pm.detach("preview")
    assert pm.state("preview") == PanelState.FLOATING
    one(fx, "show_floating", "preview")
    right = one(fx, "set_opposite_visible")
    assert right.value is True  # no overlay → right visible


# ── 7. detach(overlay) → FLOATING, right becomes visible ────────────────────
def test_detach_from_overlay():
    pm = PanelManager()
    pm.toggle("preview")  # → OVERLAY
    fx = pm.detach("preview")
    assert pm.state("preview") == PanelState.FLOATING
    one(fx, "show_floating", "preview")
    right = one(fx, "set_opposite_visible")
    assert right.value is True


# ── 8. detach(floating) → no effects ────────────────────────────────────────
def test_detach_already_floating():
    pm = PanelManager()
    pm.detach("ai")
    fx = pm.detach("ai")
    assert fx == []


# ── 9. reattach(floating) → OVERLAY, right hidden ───────────────────────────
def test_reattach_floating():
    pm = PanelManager()
    pm.detach("preview")
    fx = pm.reattach("preview")
    assert pm.state("preview") == PanelState.OVERLAY
    one(fx, "show_overlay", "preview")
    right = one(fx, "set_opposite_visible")
    assert right.value is False


# ── 10. reattach(non-floating) → no effects ─────────────────────────────────
def test_reattach_non_floating():
    pm = PanelManager()
    assert pm.reattach("preview") == []
    pm.toggle("preview")  # overlay
    assert pm.reattach("preview") == []


# ── 11. on_float_closed(floating) → HIDDEN, right visible ───────────────────
def test_on_float_closed():
    pm = PanelManager()
    pm.detach("ai")
    fx = pm.on_float_closed("ai")
    assert pm.state("ai") == PanelState.HIDDEN
    one(fx, "hide", "ai")
    right = one(fx, "set_opposite_visible")
    assert right.value is True


# ── 12. on_float_closed(non-floating) → no effects ──────────────────────────
def test_on_float_closed_non_floating():
    pm = PanelManager()
    assert pm.on_float_closed("ai") == []
    pm.toggle("ai")  # overlay
    assert pm.on_float_closed("ai") == []


# ── 13. Both floating → right visible (no overlay) ──────────────────────────
def test_both_floating_right_visible():
    pm = PanelManager()
    pm.detach("preview")
    fx = pm.detach("ai")
    right = one(fx, "set_opposite_visible")
    assert right.value is True


# ── 14. One overlay + one floating → right hidden ───────────────────────────
def test_overlay_and_floating_right_hidden():
    pm = PanelManager()
    pm.detach("ai")       # ai → FLOATING
    fx = pm.toggle("preview")  # preview → OVERLAY
    right = one(fx, "set_opposite_visible")
    assert right.value is False  # overlay is active → right hidden
