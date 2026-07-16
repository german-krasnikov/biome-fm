"""Integration tests for glass checkbox in settings."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from biome_fm.config import Config
from biome_fm.presenters.settings_presenter import SettingsPresenter
from biome_fm.views.settings_dialog import SettingsDialog


def test_settings_has_glass_checkbox(qapp, qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    assert hasattr(dlg, "_glass_cb")


def test_settings_glass_loads_false(qapp, qtbot):
    cfg = Config(glass=False)
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    SettingsPresenter(cfg, dlg, available_themes=["dark"])
    assert dlg.get_glass() is False


def test_settings_glass_loads_true(qapp, qtbot):
    cfg = Config(glass=True)
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    SettingsPresenter(cfg, dlg, available_themes=["dark"])
    assert dlg.get_glass() is True


def test_settings_glass_apply(qapp, qtbot):
    cfg = Config(glass=False)
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    sp = SettingsPresenter(cfg, dlg, available_themes=["dark"])
    dlg.set_glass(True)
    result = sp.apply()
    assert result.glass is True
