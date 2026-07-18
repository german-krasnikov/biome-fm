"""Unit tests for F316 — Accessibility Settings Tab."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_a11y_tab_exists(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    tab_texts = [d._tabs.tabText(i) for i in range(d._tabs.count())]
    assert "Accessibility" in tab_texts


def test_reduce_motion_checkbox(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    d.set_reduce_motion(True)
    assert d.get_reduce_motion() is True
    d.set_reduce_motion(False)
    assert d.get_reduce_motion() is False


def test_high_contrast_checkbox(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    d.set_high_contrast(True)
    assert d.get_high_contrast() is True


def test_presenter_loads_a11y_fields():
    from unittest.mock import MagicMock
    from biome_fm.config import Config
    from biome_fm.presenters.settings_presenter import SettingsPresenter

    cfg = Config(reduce_motion=True, high_contrast=False)
    v = MagicMock()
    v.get_theme.return_value = "dark"
    v.get_show_hidden.return_value = False
    v.get_sync_browsing.return_value = False
    v.get_file_type_colors.return_value = True
    v.get_ai_provider.return_value = "claude"
    v.get_ai_keys.return_value = ("", "")
    v.get_ollama.return_value = ("http://localhost:11434", "llama3.2")
    v.get_reduce_motion.return_value = True
    v.get_high_contrast.return_value = False

    SettingsPresenter(cfg, v)
    v.set_reduce_motion.assert_called_with(True)
    v.set_high_contrast.assert_called_with(False)


def test_presenter_saves_a11y_fields():
    from unittest.mock import MagicMock
    from biome_fm.config import Config
    from biome_fm.presenters.settings_presenter import SettingsPresenter

    cfg = Config()
    v = MagicMock()
    v.get_theme.return_value = "dark"
    v.get_show_hidden.return_value = False
    v.get_sync_browsing.return_value = False
    v.get_file_type_colors.return_value = True
    v.get_ai_provider.return_value = "claude"
    v.get_ai_keys.return_value = ("", "")
    v.get_ollama.return_value = ("http://localhost:11434", "llama3.2")
    v.get_reduce_motion.return_value = True
    v.get_high_contrast.return_value = True

    p = SettingsPresenter(cfg, v)
    result = p.apply()
    assert result.reduce_motion is True
    assert result.high_contrast is True
