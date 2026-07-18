"""F320 — System tray with context menu (tests app._build_tray helper)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture
def window(qtbot):
    from PySide6.QtWidgets import QMainWindow
    win = QMainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


def test_tray_icon_created(window):
    from biome_fm.app import _build_tray
    tray = _build_tray(window)
    assert tray is not None


def test_tray_menu_has_actions(window):
    from biome_fm.app import _build_tray
    tray = _build_tray(window)
    menu = tray.contextMenu()
    assert menu is not None
    labels = [a.text() for a in menu.actions()]
    assert any("Show" in lbl or "Hide" in lbl for lbl in labels)
    assert any("Quit" in lbl for lbl in labels)
