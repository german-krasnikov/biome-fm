"""Integration tests for F408 — Global UI Zoom (Ctrl+=/Ctrl+-/Ctrl+0)."""
import pytest

from biome_fm.app import _apply_zoom
from biome_fm.config import Config


@pytest.fixture(autouse=True)
def restore_font(qapp):
    original = qapp.font()
    yield
    qapp.setFont(original)


@pytest.fixture
def cfg(tmp_path):
    c = Config()
    c.ui_font_size = 0
    return c, tmp_path / "config.toml"


def test_zoom_in_increases_font_size(qapp, cfg):
    config, cfg_path = cfg
    f = qapp.font()
    base = f.pointSize() if f.pointSize() > 0 else 11
    _apply_zoom(qapp, config, cfg_path, base, +1)
    assert qapp.font().pointSize() == base + 1


def test_zoom_out_decreases_font_size(qapp, cfg):
    config, cfg_path = cfg
    f = qapp.font()
    base = f.pointSize() if f.pointSize() > 0 else 11
    _apply_zoom(qapp, config, cfg_path, base, -1)
    assert qapp.font().pointSize() == base - 1


def test_zoom_reset_restores_system_font(qapp, cfg):
    config, cfg_path = cfg
    system_pt = 14
    f = qapp.font()
    f.setPointSize(20)
    qapp.setFont(f)
    _apply_zoom(qapp, config, cfg_path, system_pt, 0)
    assert qapp.font().pointSize() == system_pt


def test_zoom_clamps_at_minimum(qapp, cfg):
    config, cfg_path = cfg
    f = qapp.font()
    f.setPointSize(7)
    qapp.setFont(f)
    _apply_zoom(qapp, config, cfg_path, 11, -1)
    assert qapp.font().pointSize() == 7


def test_zoom_clamps_at_maximum(qapp, cfg):
    config, cfg_path = cfg
    f = qapp.font()
    f.setPointSize(32)
    qapp.setFont(f)
    _apply_zoom(qapp, config, cfg_path, 11, +1)
    assert qapp.font().pointSize() == 32


def test_zoom_saves_to_config(qapp, cfg):
    config, cfg_path = cfg
    base = qapp.font().pointSize() if qapp.font().pointSize() > 0 else 11
    _apply_zoom(qapp, config, cfg_path, base, +2)
    assert config.ui_font_size == base + 2
