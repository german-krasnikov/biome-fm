"""Tests for SettingsPresenter."""
from unittest.mock import MagicMock

from biome_fm.config import Config
from biome_fm.presenters.settings_presenter import SettingsPresenter


def _fake_view():
    v = MagicMock()
    v.get_theme.return_value = "light"
    v.get_show_hidden.return_value = True
    v.get_sync_browsing.return_value = False
    v.get_file_type_colors.return_value = True
    v.get_ai_provider.return_value = "openai"
    v.get_ai_keys.return_value = ("key1", "key2")
    v.get_ollama.return_value = ("http://localhost:11434", "llama3.2")
    return v


def test_load_populates_view():
    cfg = Config(theme="dark", show_hidden=False)
    v = _fake_view()
    SettingsPresenter(cfg, v, available_themes=["dark", "light"])
    v.set_theme.assert_called_with("dark")
    v.set_show_hidden.assert_called_with(False)
    v.set_themes_list.assert_called_with(["dark", "light"])


def test_load_populates_plugins():
    cfg = Config()
    v = _fake_view()
    SettingsPresenter(cfg, v, available_plugins=["my-plugin"])
    v.set_plugins_list.assert_called_with(["my-plugin"])


def test_apply_updates_config():
    cfg = Config(theme="dark")
    v = _fake_view()
    p = SettingsPresenter(cfg, v)
    result = p.apply()
    assert result.theme == "light"
    assert result.show_hidden is True
    assert result.ai_default_provider == "openai"
    assert result.ai_claude_key == "key1"
    assert result.ai_openai_key == "key2"


def test_apply_returns_same_config_object():
    cfg = Config()
    v = _fake_view()
    p = SettingsPresenter(cfg, v)
    assert p.apply() is cfg


def test_apply_sync_browsing_and_colors():
    cfg = Config(sync_browsing=True, file_type_colors=False)
    v = _fake_view()
    v.get_sync_browsing.return_value = False
    v.get_file_type_colors.return_value = True
    p = SettingsPresenter(cfg, v)
    result = p.apply()
    assert result.sync_browsing is False
    assert result.file_type_colors is True
