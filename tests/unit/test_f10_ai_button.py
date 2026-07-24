"""Tests for F10 AI button in the action bar."""
from __future__ import annotations

import re


def test_f10_button_exists(qtbot):
    from biome_fm.views.action_bar import ActionBar
    bar = ActionBar()
    qtbot.addWidget(bar)
    from biome_fm.qt import QPushButton
    buttons = bar.findChildren(QPushButton)
    assert any("F10" in btn.text() for btn in buttons)


def test_ai_requested_signal(qtbot):
    from biome_fm.views.action_bar import ActionBar
    bar = ActionBar()
    qtbot.addWidget(bar)
    assert hasattr(bar, "ai_requested")


def test_f10_wiring_in_app():
    import inspect
    from biome_fm import app as app_module
    src = inspect.getsource(app_module)
    assert "bar.ai_requested.connect" in src
    assert re.search(r"QShortcut.*F10.*\.activated\.connect", src)
