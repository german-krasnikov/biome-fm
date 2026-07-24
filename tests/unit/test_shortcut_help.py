"""Unit tests for ShortcutHelpDialog."""
import biome_fm.views.shortcut_help_dialog as mod
from biome_fm.views.shortcut_help_dialog import SHORTCUTS, ShortcutHelpDialog


def test_html_contains_all_keys(qtbot):
    dlg = ShortcutHelpDialog()
    qtbot.addWidget(dlg)
    html = dlg._browser.toHtml()
    all_keys = [k for section in SHORTCUTS.values() for k in section]
    for key in all_keys:
        assert key in html, f"Missing shortcut key in dialog: {key}"


def test_section_headers_render(qtbot):
    dlg = ShortcutHelpDialog()
    qtbot.addWidget(dlg)
    html = dlg._browser.toHtml()
    for section in SHORTCUTS:
        assert section in html, f"Missing section header: {section}"


def test_empty_dict_no_crash(qtbot, monkeypatch):
    monkeypatch.setattr(mod, "SHORTCUTS", {})
    dlg = ShortcutHelpDialog()
    qtbot.addWidget(dlg)
    assert dlg._browser is not None
