"""F315 — Keyboard-Navigable Context Menu (Shift+F10)."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest


def test_shift_f10_triggers_context_menu(qtbot) -> None:
    from biome_fm.views.pane_view import PaneView

    pane = PaneView()
    qtbot.addWidget(pane)
    pane.show()

    calls = []
    pane._table.contextMenuEvent = lambda e: calls.append(e)

    QTest.keyClick(pane._table, Qt.Key.Key_F10, Qt.KeyboardModifier.ShiftModifier)

    assert len(calls) == 1


def test_menu_key_triggers_context_menu(qtbot) -> None:
    from biome_fm.views.pane_view import PaneView

    pane = PaneView()
    qtbot.addWidget(pane)
    pane.show()

    calls = []
    pane._table.contextMenuEvent = lambda e: calls.append(e)

    QTest.keyClick(pane._table, Qt.Key.Key_Menu)

    assert len(calls) == 1
