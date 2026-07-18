"""Unit tests for F309 — Reduce Motion Mode."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_config_default_false():
    from biome_fm.config import Config
    assert Config().reduce_motion is False


def test_reduce_motion_skips_animation(qtbot):
    from biome_fm.views.preview_panel import PreviewPanel
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.set_reduce_motion(True)
    # _anim must stay None when reduce_motion is on
    panel.set_visible(True)
    assert panel._anim is None


def test_no_reduce_motion_creates_animation(qtbot):
    from biome_fm.views.preview_panel import PreviewPanel
    panel = PreviewPanel()
    qtbot.addWidget(panel)
    panel.set_reduce_motion(False)
    panel.set_visible(True)
    assert panel._anim is not None
