"""Unit tests for ShortcutHelpDialog."""
import biome_fm.views.shortcut_help_dialog as mod
from biome_fm.views.shortcut_help_dialog import SHORTCUTS, ShortcutHelpDialog


def test_html_contains_all_keys(qtbot):
    dlg = ShortcutHelpDialog()
    qtbot.addWidget(dlg)
    html = dlg._browser.toHtml()
    for key in SHORTCUTS:
        assert key in html


def test_empty_dict_no_crash(qtbot, monkeypatch):
    monkeypatch.setattr(mod, "SHORTCUTS", {})
    dlg = ShortcutHelpDialog()
    qtbot.addWidget(dlg)
    assert dlg._browser is not None
