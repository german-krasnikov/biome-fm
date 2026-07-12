"""Integration tests for SettingsDialog."""
from biome_fm.views.settings_dialog import SettingsDialog


def test_dialog_creates(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    assert dlg.windowTitle() == "Settings"


def test_dialog_has_tabs(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    assert dlg._tabs.count() == 4


def test_dialog_tab_labels(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    labels = [dlg._tabs.tabText(i) for i in range(dlg._tabs.count())]
    assert labels == ["General", "Appearance", "AI", "Plugins"]


def test_dialog_protocol_methods(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    dlg.set_themes_list(["dark", "light"])
    dlg.set_theme("light")
    assert dlg.get_theme() == "light"
    dlg.set_show_hidden(True)
    assert dlg.get_show_hidden() is True
    dlg.set_show_hidden(False)
    assert dlg.get_show_hidden() is False
    dlg.set_sync_browsing(True)
    assert dlg.get_sync_browsing() is True
    dlg.set_file_type_colors(False)
    assert dlg.get_file_type_colors() is False
    dlg.set_ai_keys("k1", "k2")
    assert dlg.get_ai_keys() == ("k1", "k2")


def test_dialog_ai_provider(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    dlg.set_ai_provider("openai")
    assert dlg.get_ai_provider() == "openai"


def test_dialog_plugins_list(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    dlg.set_plugins_list(["plugin-a", "plugin-b"])
    assert dlg._plugins_list.count() == 2


def test_dialog_ollama(qtbot):
    dlg = SettingsDialog()
    qtbot.addWidget(dlg)
    dlg.set_ollama("http://host:1234", "mistral")
    assert dlg.get_ollama() == ("http://host:1234", "mistral")
