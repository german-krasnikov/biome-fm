import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QSplitter, QWidget

from biome_fm.panel_manager import PanelManager, PanelState
from biome_fm.views.panel_coordinator import PanelCoordinator


@pytest.fixture
def setup(qtbot):
    splitter = QSplitter(Qt.Orientation.Horizontal)
    left = QWidget()
    right = QWidget()
    preview = QWidget()
    ai = QWidget()
    splitter.addWidget(left)
    splitter.addWidget(right)
    splitter.addWidget(preview)
    splitter.addWidget(ai)
    preview.hide()
    ai.hide()
    qtbot.addWidget(splitter)
    splitter.show()

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


def test_toggle_preview_shows_panel_hides_right(setup):
    coord, _mgr, _splitter, _left, right, preview, _ai = setup
    coord.toggle("preview")
    assert preview.isVisible()
    assert not right.isVisible()


def test_toggle_preview_twice_hides_panel_shows_right(setup):
    coord, _mgr, _splitter, _left, right, preview, _ai = setup
    coord.toggle("preview")
    coord.toggle("preview")
    assert not preview.isVisible()
    assert right.isVisible()


def test_toggle_ai_while_preview_overlay_hides_preview_shows_ai(setup):
    coord, _mgr, _splitter, _left, _right, preview, ai = setup
    coord.toggle("preview")
    assert preview.isVisible()
    coord.toggle("ai")
    assert not preview.isVisible()
    assert ai.isVisible()


def test_detach_preview_creates_floating_dialog(setup, qtbot):
    coord, mgr, _splitter, _left, right, _preview, _ai = setup
    coord.detach("preview")
    assert mgr.state("preview") == PanelState.FLOATING
    assert "preview" in coord._float
    dlg = coord._float["preview"]
    assert isinstance(dlg, QDialog)
    assert dlg.isVisible()
    # right stays visible (no overlay)
    assert right.isVisible()
    dlg.close()


def test_float_dialog_close_returns_panel_to_hidden(setup, qtbot):
    coord, mgr, _splitter, _left, _right, preview, _ai = setup
    coord.detach("preview")
    dlg = coord._float["preview"]
    dlg.close()
    qtbot.waitUntil(lambda: mgr.state("preview") == PanelState.HIDDEN, timeout=1000)
    assert not preview.isVisible()
    assert "preview" not in coord._float


def test_state_changed_signal_fires(setup, qtbot):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    signals = []
    coord.state_changed.connect(lambda name, state: signals.append((name, state)))
    coord.toggle("preview")
    assert ("preview", "overlay") in signals


def test_save_state_returns_correct_dict(setup):
    coord, _mgr, _splitter, _left, _right, _preview, _ai = setup
    coord.toggle("preview")
    d = coord.save_state()
    assert d["preview"]["state"] == "overlay"
    assert d["ai"]["state"] == "hidden"
    assert "float_geometry" in d["preview"]


def test_restore_state_overlay(setup):
    coord, mgr, _splitter, _left, _right, preview, _ai = setup
    coord.restore_state({"preview": {"state": "overlay", "float_geometry": ""}})
    assert mgr.state("preview") == PanelState.OVERLAY
    assert preview.isVisible()


def test_restore_state_floating_creates_window(setup, qtbot):
    coord, mgr, _splitter, _left, _right, _preview, _ai = setup
    coord.restore_state({"preview": {"state": "floating", "float_geometry": ""}})
    assert mgr.state("preview") == PanelState.FLOATING
    assert "preview" in coord._float
    coord._float["preview"].close()


def test_panel_reinserted_into_splitter_after_float_close(setup, qtbot):
    coord, mgr, _splitter, _left, _right, _preview, _ai = setup
    coord.detach("preview")
    assert not coord._in_splitter["preview"]
    dlg = coord._float["preview"]
    dlg.close()
    qtbot.waitUntil(lambda: mgr.state("preview") == PanelState.HIDDEN, timeout=1000)
    assert coord._in_splitter["preview"]


def test_toggle_preview_right_active_hides_left(setup):
    coord, _, _, left, right, preview, _ = setup
    coord.toggle("preview", "right")
    assert preview.isVisible()
    assert not left.isVisible()
    assert right.isVisible()
    assert coord._splitter.indexOf(preview) == 0


def test_toggle_off_left_overlay_restores_left(setup):
    coord, _, _, left, _, preview, _ = setup
    coord.toggle("preview", "right")
    coord.toggle("preview", "right")
    assert not preview.isVisible()
    assert left.isVisible()


def test_mutual_exclusion_with_side_switch(setup):
    """Preview right-overlay, then AI left-overlay: right must be shown, left hidden."""
    coord, _, _, left, right, preview, ai = setup
    coord.toggle("preview", "left")   # right-overlay: right hidden
    assert not right.isVisible()
    coord.toggle("ai", "right")       # left-overlay: switch side
    assert not preview.isVisible()
    assert ai.isVisible()
    assert not left.isVisible()
    assert right.isVisible()           # right MUST be restored


def test_left_overlay_panel_at_index_zero(setup):
    coord, _, splitter, _, _, preview, _ = setup
    coord.toggle("preview", "right")
    assert splitter.indexOf(preview) == 0


def test_left_overlay_panel_moved_back_on_hide(setup):
    coord, _, splitter, _, _, preview, _ = setup
    coord.toggle("preview", "right")
    assert splitter.indexOf(preview) == 0
    coord.toggle("preview", "right")
    assert splitter.indexOf(preview) >= 2  # back to home position
